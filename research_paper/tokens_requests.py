import matplotlib.pyplot as plt

methods = ["Full repo (Gemini)", "Rabt"]
# 31,661 (Gemini full), 85 (Rabt)
tokens = [31661, 85]

plt.figure(figsize=(5, 4))
bars = plt.bar(methods, tokens, color=["#4c72b0", "#55a868"])
plt.ylabel("Prompt tokens per query")
plt.title("Token usage on `requests` (Who calls `request`?)")
plt.yscale("log")
plt.grid(axis="y", linestyle="--", alpha=0.4)

# Set explicit y-limits so bars and labels stay well inside the box
plt.ylim(50, 1e5)

for b, v in zip(bars, tokens):
    plt.text(b.get_x() + b.get_width() / 2, v * 1.05, f"{v}", ha="center", va="bottom", fontsize=8)

plt.tight_layout()
plt.savefig("plots/tokens_requests.png", dpi=300)
