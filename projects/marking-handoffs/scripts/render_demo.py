"""Render a 32-second tracking-only demonstration with Pillow and system FFmpeg."""
from __future__ import annotations
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG, INK, MUTED = "#f6f3ed", "#202923", "#4b5950"
PITCH, BLUE, OUT, IN = "#edf3eb", "#245d9e", "#a44f00", "#006b58"


def font(size, bold=False):
    # macOS system fonts; fallback is packaged with Pillow on other systems.
    candidates = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def choose(clips, category):
    candidates = [c for c in clips if c["split"] == "heldout" and c["category"] == category
                  and c["all_involved_detected"] and not c["ambiguous"] and not c["shared_incoming"]
                  and len(c["replay"]) >= 30]
    if not candidates:
        raise ValueError(f"No eligible demonstration clip: {category}")
    return min(candidates, key=lambda c: c["id"])


def tracking_frame(clip, k, heading):
    im = Image.new("RGB", (1280, 720), BG)
    dr = ImageDraw.Draw(im)
    dr.text((28, 18), "Marking Handoffs", font=font(36, True), fill=INK)
    dr.text((28, 65), heading, font=font(25), fill=INK)
    dr.text((28, 102), f"{clip['match']} | {clip['clock']} | 0.5x playback", font=font(18), fill=MUTED)
    box = (24, 146, 922, 644)
    patch = Image.new("RGB", (box[2]-box[0], box[3]-box[1]), PITCH)
    pd = ImageDraw.Draw(patch)
    ids = [clip["attacker_id"], clip["outgoing_id"], clip["incoming_id"]]
    pts = [p for f in clip["replay"] for p in f["players"] if p[0] in ids]
    xmin, xmax = min(p[1] for p in pts)-12, max(p[1] for p in pts)+12
    ymin, ymax = min(p[2] for p in pts)-12, max(p[2] for p in pts)+12
    scale = min((patch.width-40)/(xmax-xmin), (patch.height-40)/(ymax-ymin))
    def point(x, y):
        return (patch.width/2+(x-(xmin+xmax)/2)*scale, patch.height/2-(y-(ymin+ymax)/2)*scale)
    def rect(x, y, w, h):
        x0,y0=point(x,y+h);x1,y1=point(x+w,y)
        pd.rectangle((x0,y0,x1,y1), outline="#607668", width=2)
    rect(-52.5,-34,105,68)
    rect(-52.5,-20.16,16.5,40.32)
    rect(36,-20.16,16.5,40.32)
    pd.line([point(0,-34),point(0,34)],fill="#607668",width=2)
    cx,cy=point(0,0);r=9.15*scale
    pd.ellipse((cx-r,cy-r,cx+r,cy+r),outline="#607668",width=2)
    f = clip["replay"][k]
    lookup = {p[0]:p for p in f["players"]}
    a = lookup[clip["attacker_id"]]
    if f["assignment"] is not None:
        d = lookup[f["assignment"]]
        pd.line([point(a[1],a[2]),point(d[1],d[2])], fill=IN if d[0]==clip["incoming_id"] else OUT, width=4)
    for p in sorted(f["players"],key=lambda p:p[0] in ids):
        x,y=point(p[1],p[2]);r=13 if p[0] in ids else 6
        color=BLUE if p[3] else MUTED
        letter=None
        if p[0]==clip["attacker_id"]: color,letter=BLUE,"A"
        if p[0]==clip["outgoing_id"]: color,letter=OUT,"O"
        if p[0]==clip["incoming_id"]: color,letter=IN,"I"
        fill=color if p[4] else PITCH
        if letter=="O": pd.rectangle((x-r,y-r,x+r,y+r),fill=fill,outline=color,width=3)
        elif letter=="I": pd.polygon([(x,y-r-3),(x+r+3,y+r),(x-r-3,y+r)],fill=fill,outline=color,width=3)
        else: pd.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=color,width=2)
        if letter: pd.text((x,y),letter,font=font(15,True),fill="white" if p[4] else color,anchor="mm")
    bx,by=point(*f["ball"])
    pd.ellipse((bx-4,by-4,bx+4,by+4),fill=INK,outline="white",width=1)
    im.paste(patch,box[:2])
    dr.text((40,158),f"{f['clock']} | attack toward right",font=font(18),fill=INK)
    dr.text((948,156),"Transfer trio",font=font(22,True),fill=INK)
    for y,label,name,color in [(200,"A",clip["attacker"],BLUE),(258,"O",clip["outgoing"],OUT),(316,"I",clip["incoming"],IN)]:
        dr.text((948,y),f"{label}  {name}",font=font(20,True),fill=color)
    dr.text((948,388),f"Plausible cover: {f['cover']}",font=font(22,True),fill=INK)
    state="Unassigned" if f["assignment"] is None else "Incoming candidate" if f["assignment"]==clip["incoming_id"] else "Outgoing candidate"
    dr.text((948,424),state,font=font(19),fill=INK)
    dr.text((948,476),f"Transfer gap: {clip['longest_gap_s']:.1f} s",font=font(19),fill=INK)
    dr.text((948,513),"Hollow = extrapolated",font=font(17),fill=MUTED)
    dr.text((948,545),"Trio detected throughout",font=font(17),fill=MUTED)
    dr.text((948,570),"the transfer window.",font=font(17),fill=MUTED)
    context = "Before measured window" if f["frame"] < clip["window_start_frame"] else "After measured window" if f["frame"] >= clip["window_end_frame_exclusive"] else "Inside measured window"
    dr.text((948,610),context,font=font(17),fill=MUTED)
    dr.text((28,663),"Candidate handoffs only. Geometry cannot establish coaching responsibility.",font=font(20),fill=INK)
    dr.text((28,695),"Data: SkillCorner Open Data (MIT). Tracking only; no broadcast footage. Display 5 Hz.",font=font(15),fill=MUTED)
    return im


def card(title, lines):
    im=Image.new("RGB",(1280,720),BG);dr=ImageDraw.Draw(im)
    dr.text((64,76),"Marking Handoffs",font=font(28),fill=MUTED)
    dr.text((64,160),title,font=font(44,True),fill=INK)
    for i,line in enumerate(lines):
        dr.text((64,260+i*65),line,font=font(27),fill=INK)
    dr.text((64,658),"SkillCorner Open Data (MIT) | Two-match research pilot | Candidate responsibility only",font=font(18),fill=MUTED)
    return im


def main():
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg: raise RuntimeError("Install open-source FFmpeg to render the MP4")
    clips=json.loads((ROOT/"outputs/replays.json").read_text())
    continuous,gap=choose(clips,"continuous"),choose(clips,"gap")
    manifest=dict(duration_s=32, fps=20, dimensions=[1280,720], continuous=continuous["id"],gap=gap["id"],
                  selection="First lexicographic ID per category, held-out, detected trio, >=30 replay frames, no ambiguity/shared flag",
                  playback="0.5x source time, positions displayed at 5 Hz, output encoded at 20 fps")
    (ROOT/"outputs/demo-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    h=json.loads((ROOT/"outputs/results.json").read_text())["splits"]["heldout"]
    intro=card("Who takes over?",["A defender leaves. Another becomes the plausible cover.","Does a temporary geometric gap appear?", "Two real tracking examples, shown at half speed.","These are candidate handoffs, not verified assignments."])
    outro=card("Fewer switches. Tactical accuracy unknown.",[f"Held-out candidates: {sum(h['candidate_counts'].values())} ({h['candidate_counts']['gap']} with >=0.4 s gaps).",
                f"Identity changes / attacker-min: {h['nearest']['identity_changes_per_attacker_minute']:.2f} to {h['proposed']['identity_changes_per_attacker_minute']:.2f}.",
                f"Assignment availability: {100*h['proposed']['assigned_fraction']:.1f}%. Short runs: {h['nearest']['short_assignment_runs']} to {h['proposed']['short_assignment_runs']}.",
                "The fewer-short-runs hypothesis failed. Expert labels needed."])
    output=ROOT/"outputs/marking-handoffs-demo.mp4"
    command=[ffmpeg,"-y","-loglevel","error","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24","-s","1280x720","-r","20","-i","-","-an","-c:v","libx264","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    for index in range(640):
        t=index/20
        if t<4: im=intro
        elif t<16: im=tracking_frame(continuous,min(len(continuous["replay"])-1,int((t-4)/.4)),"Continuous cover in the measured transfer window")
        elif t<28: im=tracking_frame(gap,min(len(gap["replay"])-1,int((t-16)/.4)),"A temporary geometric coverage gap")
        else: im=outro
        if index in [0,200,400,600]: im.save(ROOT/f"outputs/demo-frame-{index:03d}.png")
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    if proc.wait(): raise RuntimeError("FFmpeg failed")
    print(output)


if __name__=="__main__": main()
