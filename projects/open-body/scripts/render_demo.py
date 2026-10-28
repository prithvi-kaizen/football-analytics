"""Render a 30-second, silent MP4 from the same real clips used by the viewer."""

from pathlib import Path
import json
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import findfont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
D = json.loads((OUT / "viewer_data.json").read_text())
R = D["results"]
PAPER = "#f6f4ee"
INK = "#202b27"
GREEN = "#204f3d"
ORANGE = "#a44208"
BLUE = "#164b87"
FONT = findfont("DejaVu Sans")
FONTS = {s: ImageFont.truetype(FONT, s) for s in [16, 18, 20, 22, 24, 28, 30, 34, 42]}


def txt(draw, xy, text, size=22, fill=INK):
    draw.text(xy, text, font=FONTS[size], fill=fill)


def ellipse(draw, centre, r, fill, outline=None, width=2):
    x, y = centre
    draw.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=width)


def scene(clip, frame):
    im = Image.new("RGB", (1280, 720), PAPER)
    d = ImageDraw.Draw(im)
    txt(d, (30, 18), "Open Body", 34)
    txt(d, (30, 65), clip["fixture"] + "  |  " + clip["player_name"], 22)
    box = (30, 123, 860, 650)
    d.rectangle(box, fill=GREEN)
    scale = min(790 / clip["pitch_length"], 440 / clip["pitch_width"])
    cx = 445
    cy = 388

    def xy(x, y):
        return cx + x * scale, cy - y * scale

    left, top = xy(-clip["pitch_length"] / 2, clip["pitch_width"] / 2)
    right, bottom = xy(clip["pitch_length"] / 2, -clip["pitch_width"] / 2)
    d.rectangle([left, top, right, bottom], outline="#e7eee5", width=2)
    d.line(
        [xy(0, -clip["pitch_width"] / 2), xy(0, clip["pitch_width"] / 2)],
        fill="#e7eee5",
        width=2,
    )
    rr = 9.15 * scale
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline="#e7eee5", width=2)
    for side in [-1, 1]:
        goal = side * clip["pitch_length"] / 2
        a, b = xy(goal if side < 0 else goal - 16.5, 20.16)
        c, e = xy(goal + 16.5 if side < 0 else goal, -20.16)
        d.rectangle([a, b, c, e], outline="#e7eee5", width=2)
    for p in frame["players"]:
        selected = p["id"] == clip["player_id"]
        point = xy(p["x"], p["y"])
        fill = (
            "#ffac62"
            if selected
            else (BLUE if p["home"] else "#fff")
            if p["detected"]
            else GREEN
        )
        ellipse(d, point, 11 if selected else 8, fill, "#fff", 2)
    selected = next((p for p in frame["players"] if p["id"] == clip["player_id"]), None)
    if selected and frame["heading"] is not None:
        x, y = xy(selected["x"], selected["y"])
        a = frame["heading"]
        ex = x + math.cos(a) * 40
        ey = y - math.sin(a) * 40
        d.line([(x, y), (ex, ey)], fill="#ffac62", width=6)
        for off in [-0.5, 0.5]:
            d.line(
                [(ex, ey), (ex - 12 * math.cos(a + off), ey + 12 * math.sin(a + off))],
                fill="#ffac62",
                width=5,
            )
    if frame["ball"]:
        ellipse(d, xy(*frame["ball"]), 5, "#fff", INK, 2)
    txt(
        d,
        (46, 133),
        "Attack " + ("right" if clip["attack_sign"] == 1 else "left"),
        18,
        "#fff",
    )
    txt(d, (46, 616), f"t = {frame['t']:+.2f} s from reception", 22, "#fff")
    d.rectangle((890, 123, 1250, 650), fill="#edece5", outline="#7b827a", width=1)
    txt(d, (910, 138), "Player-centred 3D pose", 22)
    yaw = math.radians(35)

    def proj(v):
        return (
            1070 + (math.cos(yaw) * v[0] - math.sin(yaw) * v[1]) * 135,
            390 + (math.sin(yaw) * v[0] + math.cos(yaw) * v[1]) * 45 - v[2] * 155,
        )

    if frame["joints"]:
        for a, b in D["skeleton"]:
            if a in frame["joints"] and b in frame["joints"]:
                d.line(
                    [proj(frame["joints"][a]), proj(frame["joints"][b])],
                    fill=ORANGE if [a, b] == ["lShoulder", "rShoulder"] else GREEN,
                    width=7 if [a, b] == ["lShoulder", "rShoulder"] else 4,
                )
        for v in frame["joints"].values():
            ellipse(d, proj(v), 2, GREEN)
    else:
        txt(d, (920, 370), "Pose unavailable", 22)
    txt(d, (910, 585), frame["pose_status"].replace("_", " "), 16)
    txt(d, (910, 616), "Z is relative to the hip", 18)
    txt(
        d,
        (30, 672),
        "Orange: receiver + raw shoulders. Shoulder heading is not gaze or intention.",
        20,
    )
    return im


def result_image():
    im = Image.new("RGB", (1280, 720), PAPER)
    d = ImageDraw.Draw(im)
    r = R["primary"]
    rev = R["reverse_diagnostic"]
    c = r["delta_log_loss_95ci"]
    txt(d, (60, 42), "A promising point estimate. An inconclusive pilot.", 34)
    txt(
        d,
        (60, 110),
        f"Chronological holdout: {r['train_n']} training / {r['baseline']['n']} test receptions",
        24,
    )
    txt(d, (60, 175), "Position + pressure", 28)
    txt(d, (750, 175), f"Log loss {r['baseline']['log_loss']:.4f}", 30)
    txt(d, (60, 230), "+ shoulder orientation", 28)
    txt(d, (750, 230), f"Log loss {r['orientation']['log_loss']:.4f}", 30, ORANGE)
    txt(
        d,
        (60, 315),
        f"Change: {r['delta_log_loss']:+.4f}; conditional 95% interval [{c['low']:+.4f}, {c['high']:+.4f}]",
        28,
    )
    txt(d, (60, 370), "The interval includes zero. The pilot criterion is not met.", 24)
    txt(
        d,
        (60, 425),
        f"Reverse split change: {rev['delta_log_loss']:+.4f}; its interval also includes zero.",
        24,
    )
    txt(
        d,
        (60, 480),
        "Midfield-only check: worse in one direction, better in the other.",
        24,
    )
    txt(d, (60, 560), "Two matches cannot establish a general or causal benefit.", 28)
    txt(
        d,
        (60, 635),
        "Data: SkillCorner / PySport (MIT). Full code, audits and held-out predictions included.",
        20,
    )
    return im


def chart():
    fig, ax = plt.subplots(figsize=(9, 4.2))
    fig.subplots_adjust(left=0.28, right=0.97, top=0.85, bottom=0.25)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    for i, (name, r) in enumerate(
        [
            ("Chronological holdout", R["primary"]),
            ("Reverse diagnostic", R["reverse_diagnostic"]),
        ]
    ):
        c = r["delta_log_loss_95ci"]
        value = r["delta_log_loss"]
        ax.errorbar(
            value,
            1 - i,
            xerr=[[value - c["low"]], [c["high"] - value]],
            fmt="o",
            color=ORANGE,
            ecolor=GREEN,
            capsize=6,
            markersize=8,
            lw=2,
        )
        ax.annotate(
            f"{value:+.4f} [{c['low']:+.4f}, {c['high']:+.4f}]",
            (value, 1 - i),
            xytext=(0, 17),
            textcoords="offset points",
            ha="center",
            fontsize=10,
        )
    ax.axvline(0, color="#7b827a", lw=1)
    ax.set_yticks(
        [1, 0],
        ["Chronological holdout\n(test 1996435)", "Reverse diagnostic\n(test 1925299)"],
    )
    ax.set_ylim(-0.6, 1.7)
    ax.set_xlim(-0.04, 0.014)
    ax.set_xlabel("Orientation minus baseline log loss (negative favours orientation)")
    ax.set_title("Both conditional 95% intervals include zero", loc="left", pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(
        0.03,
        0.01,
        "Paired 5-minute block bootstrap, 2,000 resamples. Conditional on one test match, not new matches.",
        fontsize=9,
        color="#49554f",
    )
    fig.savefig(OUT / "results.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    chart()
    fps = 15
    seconds = 30
    path = OUT / "open-body-demo.mp4"
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        "1280x720",
        "-framerate",
        str(fps),
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(path),
    ]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    ending = result_image()
    for i in range(seconds * fps):
        t = i / fps
        if t < 4:
            clip = D["clips"][0]
            frame = min(clip["frames"], key=lambda f: abs(f["t"]))
            im = scene(clip, frame)
            draw = ImageDraw.Draw(im)
            draw.rectangle((30, 185, 860, 320), fill=PAPER)
            txt(draw, (50, 202), "Can shoulders tell us more at reception?", 30)
            txt(draw, (50, 257), "A two-match, open-data measurement experiment", 22)
        elif t < 20:
            which = 0 if t < 12 else 1
            local = (t - (4 if which == 0 else 12)) * 0.5
            clip = D["clips"][which]
            target = -1 + local
            frame = min(clip["frames"], key=lambda f: abs(f["t"] - target))
            im = scene(clip, frame)
        else:
            im = ending
        proc.stdin.write(im.tobytes())
        if i in [45, 120, 240, 360]:
            im.save(OUT / f"demo-check-{i:03}.png")
    proc.stdin.close()
    assert proc.wait() == 0
    print(path)
