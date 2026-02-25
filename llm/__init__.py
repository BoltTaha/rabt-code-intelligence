"""
LLM integration: prompt building and API client.
Uses Google Gemini (google-genai SDK) when GEMINI_API_KEY is set; otherwise returns a stub response.
"""

import os


def answer_with_llm(subgraph_text: str, query: str, config: dict) -> tuple[str, str, dict]:
    """
    Return (answer, confidence, usage_info) using the minimal subgraph as context.
    confidence in ("HIGH", "MEDIUM", "LOW").
    usage_info has prompt_tokens, total_tokens when available from the API.
    If GEMINI_API_KEY is not set or the API fails, returns a stub response.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return (
            f"(LLM not configured; set GEMINI_API_KEY. Subgraph had {len(subgraph_text)} chars.)",
            "MEDIUM",
            {"prompt_tokens": None, "total_tokens": None},
        )

    try:
        from google import genai
    except ImportError:
        return (
            f"(Install google-genai: pip install google-genai. Subgraph had {len(subgraph_text)} chars.)",
            "MEDIUM",
            {"prompt_tokens": None, "total_tokens": None},
        )

    model_name = (config.get("llm") or {}).get("model") or "gemini-2.5-flash-lite"

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""You are a code dependency expert. Answer based ONLY on the context provided.

Context (dependency graph slice):
{subgraph_text}

User question: {query}

Answer in one or two short sentences. Do not invent information not present in the context."""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        # Extract text from response (SDK may use .text or .candidates)
        if hasattr(response, "text") and response.text:
            answer = response.text.strip()
        elif getattr(response, "candidates", None) and len(response.candidates) > 0:
            part = response.candidates[0].content.parts[0]
            answer = (getattr(part, "text", None) or "").strip()
        else:
            answer = "(No response from model.)"

        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            u = response.usage_metadata
            usage["prompt_tokens"] = getattr(u, "prompt_token_count", None) or getattr(u, "input_token_count", None)
            usage["total_tokens"] = getattr(u, "total_token_count", None)
        else:
            usage["prompt_tokens"] = None
            usage["total_tokens"] = None

        return (answer or "(No response from model.)", "HIGH" if subgraph_text else "MEDIUM", usage)
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            return (
                "(Gemini quota exceeded or rate limit. Wait ~1 minute and try again, or change config llm.model to e.g. gemini-2.5-flash. See https://ai.google.dev/gemini-api/docs/rate-limits.)",
                "LOW",
                {"prompt_tokens": None, "total_tokens": None},
            )
        return (
            f"(LLM error: {e!s}. Subgraph had {len(subgraph_text)} chars.)",
            "LOW",
            {"prompt_tokens": None, "total_tokens": None},
        )


__all__ = ["answer_with_llm"]
