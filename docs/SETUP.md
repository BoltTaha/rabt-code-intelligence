# Setup — Semantic Graph Memory

Your system needs either a working virtual environment or the right Python packages. Use **Option A** (recommended) or **Option B**.

---

## Option A: Fix venv (recommended)

The error `ensurepip is not available` / `.venv/bin/python3: No such file or directory` means the **venv** support package is not installed. Install it once, then create the venv:

```bash
# 1. Install venv support (one-time; enter your password when asked)
sudo apt install python3.12-venv

# 2. Go to project and remove any broken venv
cd ~/Desktop/Startup
rm -rf .venv

# 3. Create a fresh venv
python3 -m venv .venv

# 4. Activate and install dependencies
source .venv/bin/activate
pip install -r requirements.txt

# 5. Every time you open a new terminal: activate the venv, then run
source .venv/bin/activate
python examples/sample_repo/main.py   # appends to .runtime_events.jsonl
python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
# Pipeline loads config/default.yaml by default (runtime.main_module, LLM).
```

---

## Option B: Run without venv (system packages)

If you cannot use `sudo` or prefer not to use a venv, install the dependencies via apt and run with `python3`:

```bash
# 1. Install packages (one-time; needs sudo)
sudo apt install python3-networkx python3-yaml python3-pytest

# 2. Run from project root (no activate needed)
cd ~/Desktop/Startup
PYTHONPATH=. python3 run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
```

Note: System packages may be slightly older than in `requirements.txt`. If something fails, use Option A.

---

## Optional: Gemini LLM (natural-language answers)

To get real AI-generated answers, put your **Google Gemini API key** in a **local `.env` file**. That file is **editable only on your machine** and is **never pushed to GitHub** (it is in `.gitignore`).

### 1. Create and edit `.env` (local only)

```bash
cd ~/Desktop/Startup
cp .env.example .env
# Edit .env and replace your_key_here with your real Gemini API key (e.g. from Google AI Studio)
```

After that, the pipeline loads `GEMINI_API_KEY` from `.env` automatically when you run `run_pipeline.py` (via `python-dotenv` at startup). You do not need to `export` the key or source `.env` manually. You can edit `.env` anytime; it will never be committed.

### 2. Gemini free tier (what to expect)

| Limit | Free tier (typical) |
|-------|----------------------|
| **Requests per minute (RPM)** | About 10–15 for Gemini Flash |
| **Tokens per minute (TPM)** | 250,000 total |
| **Requests per day** | 100–1,000 depending on model |
| **Response time** | Often **0.5–2 seconds** per query |

So for Rabt: each time you run a query with `-q "..."`, that is **one request**. A few runs per minute are fine; avoid dozens in a row. Get a free key at [Google AI Studio](https://aistudio.google.com/apikey).

---

## Quick check

After setup, this should print node/edge counts and a subgraph:

```bash
# With venv (Option A):
source .venv/bin/activate
python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"

# Without venv (Option B):
PYTHONPATH=. python3 run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
```
