"""Render a silent, original 35-second animated schematic; no broadcast footage."""
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "media/demo.mp4"
W, H, FPS, DURATION = 1280, 720, 15, 35
BG, INK, MUTED, ACCENT, GREEN = "#f6f3eb", "#172c35", "#52646b", "#b14d2c", "#254c50"


def font(size, bold=False):
    path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"
    return ImageFont.truetype(path, size)


def line(d, text, xy, size, color=INK, bold=False):
    d.text(xy, text, font=font(size, bold), fill=color)


def frame(t):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    line(d, "FOOTBALL ANALYTICS  /  EVENT SEQUENCES", (70, 42), 23, ACCENT, True)
    d.line((70, 91, 1210, 91), fill="#c9d0ca", width=2)
    if t < 7:
        line(d, "THE CORNER THAT", (70, 155), 72, INK, True)
        line(d, "NEVER ENDED", (70, 245), 72, GREEN, True)
        line(d, "A defender's touch is not a change of possession.", (72, 390), 34)
        line(d, "817 historical corners  /  82 Euro matches", (72, 485), 26, MUTED)
        d.rectangle((70, 580, 70 + int(1140 * min(t/7, 1)), 592), fill=ACCENT)
    elif t < 19:
        line(d, "One real sequence: Croatia v Italy, 2024", (70, 125), 39, INK, True)
        line(d, "Minute 26 · schematic positions, observed event order", (72, 179), 24, MUTED)
        # The pitch and positions are illustrative; the timestamp order comes from the data.
        d.rounded_rectangle((75, 248, 1200, 585), radius=8, outline=GREEN, width=4)
        d.line((638, 248, 638, 585), fill=GREEN, width=3)
        d.ellipse((568, 345, 708, 485), outline=GREEN, width=3)
        d.rectangle((1020, 312, 1200, 522), outline=GREEN, width=3)
        pts=[(1160,280),(990,360),(810,390),(1010,420),(1085,397)]
        labels=["Delivery","Clearance","Second ball","Box entry","Shot"]
        label_points=[(1070,289),(910,320),(728,419),(930,454),(1095,415)]
        start=[7,9.2,11.2,14.2,16.7]
        for i,p in enumerate(pts):
            if t>=start[i]:
                if i: d.line((*pts[i-1],*p),fill=ACCENT,width=8)
                d.ellipse((p[0]-13,p[1]-13,p[0]+13,p[1]+13),fill=ACCENT)
                line(d,labels[i],label_points[i],22,INK,True)
        line(d, "Clearance at +1.33s  →  recovery at +3.17s  →  shot at +7.24s", (72, 625), 25, INK)
    elif t < 27:
        line(d, "What 15 seconds reveals", (70, 140), 58, INK, True)
        stats=[("47.6%","attacking action after contact"),("15.3%","corner with a recovered second-phase shot"),("75","shots with phase unresolved")]
        for i,(v,label) in enumerate(stats):
            y=280+i*110
            d.rectangle((70,y-8,1200,y+85),fill="#e8ece6" if i!=1 else "#ead9ce")
            line(d,v,(95,y),57,ACCENT if i==1 else GREEN,True)
            line(d,label,(370,y+19),27,INK)
    else:
        line(d, "A touch is not a turnover.", (70, 172), 60, INK, True)
        line(d, "A clearance is not confirmed control.", (70, 260), 48, GREEN)
        line(d, "Historical Euros, not a 2026/27 rule-change effect.", (70, 380), 31, MUTED)
        line(d, "Explore the window, flow and real examples on the portfolio.", (70, 495), 28, ACCENT)
        line(d, "StatsBomb Open Data · original schematic animation", (70, 620), 20, MUTED)
    d.rectangle((70, 675, 1210, 681),fill="#d9ddd4")
    d.rectangle((70, 675, 70+int(1140*t/DURATION), 681),fill=ACCENT)
    return im


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-pix_fmt","yuv420p","-crf","21","-movflags","+faststart",str(OUT)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    for i in range(FPS*DURATION):
        p.stdin.write(frame(i/FPS).tobytes())
    p.stdin.close()
    err=p.stderr.read().decode()
    if p.wait():
        raise RuntimeError(err[-1500:])
    print(OUT)


if __name__=="__main__":
    main()
