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

# 5. Run the pipeline
python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
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

## Quick check

After setup, this should print node/edge counts and a subgraph:

```bash
# With venv (Option A):
source .venv/bin/activate
python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"

# Without venv (Option B):
PYTHONPATH=. python3 run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
```
