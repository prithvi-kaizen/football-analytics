"""Optional publication figure; values are read from the frozen results."""
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"outputs/.mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

h=json.loads((ROOT/"outputs/results.json").read_text())["splits"]["heldout"]
fig,axes=plt.subplots(1,3,figsize=(12,4.6),layout="constrained")
fig.patch.set_facecolor("#f6f3ed")
settings=[("Identity changes / attacker-minute","identity_changes_per_attacker_minute",1),
          ("Assigned eligible frames (%)","assigned_fraction",100),
          ("Short interior assignment runs","short_assignment_runs",1)]
for ax,(title,key,scale) in zip(axes,settings):
    vals=[h[m][key]*scale for m in ["nearest","proposed"]]
    bars=ax.bar(["Nearest","Proposed"],vals,color=["#4b5950","#006b58"],width=.6)
    ax.set_title(title,fontsize=11,pad=16)
    ax.set_ylim(0,max(vals)*1.25)
    if scale == 100:
        ax.set_ylim(0,110)
        ax.set_yticks([0,25,50,75,100])
    ax.spines[["top","right"]].set_visible(False)
    ax.bar_label(bars,labels=[f"{v:.2f}" if key!="short_assignment_runs" else str(int(v)) for v in vals],padding=5)
    ax.set_facecolor("#f6f3ed")
fig.suptitle("Fewer identity changes, more short runs on the held-out match",fontsize=15)
fig.supxlabel("105,492 eligible attacker-frames. Lower switching is not tactical accuracy; proposed assignment availability is 53.6%.",fontsize=9)
fig.savefig(ROOT/"outputs/heldout-results.png",dpi=180)
fig.savefig(ROOT/"outputs/heldout-results.svg")
print("Saved heldout-results.png and .svg")
