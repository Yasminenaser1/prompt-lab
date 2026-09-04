import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

splits = ["train", "dev", "test\n(held out)"]
base = [0.250, 0.167, 0.250]
best = [0.700, 0.667, 0.875]
x = range(len(splits))
w = 0.36
ax1.bar([i - w/2 for i in x], base, w, label="base prompt", color="#b0b7c3")
ax1.bar([i + w/2 for i in x], best, w, label="bootstrap k=3", color="#3b6ea5")
ax1.set_xticks(list(x)); ax1.set_xticklabels(splits)
ax1.set_ylim(0, 1); ax1.set_ylabel("mean field accuracy")
ax1.set_title("Optimized vs base prompt")
ax1.legend(frameon=False)

methods = ["base", "bootstrap", "mutate", "append", "human\nrule"]
scores  = [0.167, 0.667, 0.583, 0.667, 0.583]
lo      = [0.167, 0.667, 0.083, 0.583, 0.583]
colors  = ["#b0b7c3", "#3b6ea5", "#c98a3f", "#c98a3f", "#8f8f8f"]
ax2.bar(methods, scores, color=colors)
for i, (s, l) in enumerate(zip(scores, lo)):
    if l < s:
        ax2.vlines(i, l, s, color="#333", lw=1.4)
        ax2.hlines([l, s], i - 0.1, i + 0.1, color="#333", lw=1.4)
ax2.set_ylim(0, 1); ax2.set_ylabel("dev score")
ax2.set_title("Best per method (bars = worst-to-best range)")

plt.tight_layout()
plt.savefig("results.png", dpi=150)
print("wrote results.png")
