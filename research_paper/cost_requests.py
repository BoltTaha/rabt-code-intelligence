import matplotlib.pyplot as plt

methods = ["GPT-4o full", "GPT-4o Rabt", "o1 full", "o1 Rabt"]
costs = [79.15, 0.13, 474.90, 0.75]

plt.figure(figsize=(6, 4))
bars = plt.bar(methods, costs, color=["#4c72b0", "#4c72b0", "#dd8452", "#dd8452"])
plt.ylabel("Cost per 1,000 queries (USD)")
plt.title("Estimated cost on `requests` (Who calls `request`?)")
plt.yscale("log")
plt.grid(axis="y", linestyle="--", alpha=0.4)

for b, v in zip(bars, costs):
    plt.text(b.get_x() + b.get_width() / 2, v * 1.1, f"${v:.2f}", ha="center", va="bottom", fontsize=8)

plt.tight_layout()
plt.savefig("plots/cost_requests.png", dpi=300)
