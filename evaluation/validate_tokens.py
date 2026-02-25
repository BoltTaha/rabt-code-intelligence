"""
Validate token counts: make real Gemini API calls and print usage_metadata.
Use this to verify the numbers in baseline_comparison match what the API returns.

Run: python -m evaluation.validate_tokens --repo examples/requests_repo --query "Who calls request?"

Compare the output with:
  - baseline_comparison script output
  - Google AI Studio dashboard (Usage / Input tokens per model)
"""

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass


def _full_repo_context(repo_path: str | Path) -> str:
    repo = Path(repo_path).resolve()
    if not repo.exists():
        return ""
    parts = []
    for py in sorted(repo.rglob("*.py")):
        if ".venv" in str(py) or "__pycache__" in str(py):
            continue
        try:
            parts.append(f"# --- {py.relative_to(repo)} ---\n{py.read_text(encoding='utf-8')}")
        except (OSError, ValueError):
            continue
    return "\n\n".join(parts)


def _call_and_print_usage(label: str, prompt: str, config: dict) -> bool:
    """Call Gemini, print raw usage_metadata. Return True if successful."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print(f"{label}: GEMINI_API_KEY not set", file=sys.stderr)
        return False

    try:
        from google import genai
    except ImportError:
        print(f"{label}: google-genai not installed", file=sys.stderr)
        return False

    model_name = (config.get("llm") or {}).get("model") or "gemini-2.5-flash-lite"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)

        print(f"\n{label}")
        print("-" * 50)
        print(f"  Prompt length: {len(prompt)} chars")
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            u = response.usage_metadata
            pt = getattr(u, "prompt_token_count", None) or getattr(u, "input_token_count", None)
            ot = getattr(u, "candidates_token_count", None) or getattr(u, "output_token_count", None)
            tt = getattr(u, "total_token_count", None)
            print(f"  prompt_token_count / input_token_count: {pt}")
            print(f"  candidates_token_count / output_token_count: {ot}")
            print(f"  total_token_count: {tt}")
            print(f"  Raw usage_metadata: {u}")
        else:
            print("  usage_metadata: (not available)")
        return True
    except Exception as e:
        print(f"{label}: Error: {e}", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate token counts from Gemini API")
    ap.add_argument("--repo", "-r", default=str(_ROOT / "examples" / "requests_repo"), help="Repo path")
    ap.add_argument("--query", "-q", default="Who calls request?", help="Question")
    ap.add_argument("--config", "-c", help="Config YAML path")
    args = ap.parse_args()

    from run_pipeline import load_config

    config = load_config(args.config)
    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"Repo not found: {repo}", file=sys.stderr)
        return 1

    full_context = _full_repo_context(args.repo)
    full_prompt = f"""You are a code dependency expert. Answer based on the following full codebase.

Codebase:
{full_context[:120000]}

User question: {args.query}

Answer in one or two short sentences. Be precise."""

    # Call 1: Full repo
    ok1 = _call_and_print_usage("Full repo context (Gemini)", full_prompt, config)

    # Get Rabt subgraph
    from run_pipeline import run

    result = run(repo_path=args.repo, query=args.query, config_path=args.config, persist=True)
    subgraph_text = result.get("subgraph_text", "") or "(empty)"

    rabt_prompt = f"""You are a code dependency expert. Answer based ONLY on the context provided.

Context (dependency graph slice):
{subgraph_text}

User question: {args.query}

Answer in one or two short sentences. Do not invent information not present in the context."""

    # Call 2: Rabt subgraph
    ok2 = _call_and_print_usage("Rabt minimal subgraph", rabt_prompt, config)

    print("\n" + "=" * 60)
    print("Validation summary")
    print("=" * 60)
    print("1. Compare the prompt_token_count values above with baseline_comparison output.")
    print("2. In Google AI Studio (aistudio.google.com) → Usage:")
    print("   - Each run adds 2 API calls (full + Rabt).")
    print("   - Dashboard shows AGGREGATE usage (all calls, possibly multiple runs).")
    print("   - So you may see ~31k + ~50 + ... from several runs = larger total.")
    print("3. The script numbers are AUTHORITATIVE for each single call.")
    print("   AI Studio sums everything; use this script for precise per-call validation.")
    print()

    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
