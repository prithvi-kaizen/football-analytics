"""Static research diagnostics. Labels and units are explicit; no hosted renderer."""
import matplotlib.pyplot as plt
import numpy as np


def metric_plot(table, path):
    scenarios = list(dict.fromkeys(table.scenario))
    colors = {"nearest": "#777777", "state_machine": "#0072B2", "hmm": "#D55E00"}
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, layout="constrained")
    for ax, metric, title in zip(axes, ["macro_f1", "spell_f1"], ["Frame macro F1", "Possession spell F1"]):
        for j, method in enumerate(colors):
            data = table[table.method == method].groupby("scenario")[metric].agg(["mean", "std"]).reindex(scenarios)
            ax.bar(np.arange(len(scenarios)) + (j - 1) * 0.25, data["mean"], width=0.24,
                   yerr=data["std"].fillna(0), capsize=2, label=method, color=colors[method])
        ax.set(ylabel=title, ylim=(0, 1.08))
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(loc="upper right", ncols=3, fontsize=9)
    axes[-1].set_xticks(np.arange(len(scenarios)), [x.replace("_", "\n") for x in scenarios], fontsize=9)
    fig.suptitle(f"Synthetic stress tests only | mean ± seed standard deviation ({table.seed.nunique()} seeds)")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def diagnostic_plot(timelines, path):
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    names = [n for n in ("occlusion", "transition_blind", "stationary_live", "invisible_stoppages") if n in timelines]
    if not names:
        names = list(timelines)[:4]
    fig, axes = plt.subplots(len(names), 1, figsize=(13, 2.4 * len(names)), sharex=True,
                             squeeze=False, layout="constrained")
    code = {"H": 0, "A": 1, "D": 2, "X": 3}
    colors = ["#0072B2", "#D55E00", "#777777", "#eeeeee", "#222222"]
    for ax, name in zip(axes[:, 0], names):
        time, truth, predictions, observed = timelines[name]
        series = {"truth": truth, **predictions}
        raster = np.vstack([[code[x] for x in values] for values in series.values()]
                           + [np.where(observed, 3, 4)])
        dt = time[1] - time[0] if len(time) > 1 else 0.04
        ax.imshow(raster, aspect="auto", interpolation="nearest", cmap=ListedColormap(colors),
                  vmin=0, vmax=4, extent=(time[0], time[-1] + dt, 4.5, -0.5))
        ax.set(yticks=np.arange(5), yticklabels=[*series, "ball missing"],
               title=name.replace("_", " "))
        for edge in np.arange(0.5, 4.5):
            ax.axhline(edge, color="white", lw=2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.legend(handles=[Patch(facecolor=colors[j], label=x) for j, x in enumerate(["H", "A", "D", "X", "missing ball"])],
               ncols=5, loc="outside upper right", fontsize=9)
    axes[-1, 0].set_xlabel("Synthetic time (seconds); a colour change marks a predicted boundary")
    fig.suptitle("Synthetic failure modes | first configured seed", x=0.01, ha="left")
    fig.savefig(path, dpi=160)
    plt.close(fig)
