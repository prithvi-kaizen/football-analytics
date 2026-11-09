"""Render the observed Adelaide example deterministically. No invented coordinates."""
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
W,H,FPS,DURATION=1600,900,30,32
BG='#f5f3ed'; INK='#273c45'; BLUE='#245a79'; AMBER='#935000'; PITCH='#e8eee4'; MARK='#718575'

def font(size,serif=False):
    choices=([Path('/System/Library/Fonts/Supplemental/Georgia.ttf')] if serif else [Path('/System/Library/Fonts/Supplemental/Arial.ttf')])+[Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    for p in choices:
        if p.exists(): return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)

def text(d,xy,s,size=26,color=INK,serif=False):
    d.text(xy,s,font=font(size,serif),fill=color)

def frame(t,e):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    # Two-layer pitch and paper surface are fixed; the actual players carry the motion.
    left,top,pw,ph=85,205,1050,680
    def pos(x,y): return left+(x+52.5)*10,top+(34-y)*10
    d.rounded_rectangle([left-10,top-10,left+pw+10,top+ph+10],8,fill=PITCH)
    d.rectangle([left,top,left+pw,top+ph],outline=MARK,width=2)
    d.line([pos(0,-34),pos(0,34)],fill=MARK,width=2)
    cx,cy=pos(0,0); r=91.5;d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=MARK,width=2)
    for x,sgn in [(-52.5,1),(52.5,-1)]:
        a=pos(x,20.16);b=pos(x+sgn*16.5,-20.16);d.rectangle([min(a[0],b[0]),a[1],max(a[0],b[0]),b[1]],outline=MARK,width=2)
        a=pos(x,9.16);b=pos(x+sgn*5.5,-9.16);d.rectangle([min(a[0],b[0]),a[1],max(a[0],b[0]),b[1]],outline=MARK,width=2)
    if t<4: source_t=0
    elif t<12: source_t=(t-4)/8*6.1
    elif t<23: source_t=min(1.3,(t-12)*.22)
    elif t<29: source_t=1.3+(t-23)/6*4.8
    else: source_t=6.1
    i=min(len(e['frames'])-1,round(source_t*10));f=e['frames'][i]
    x,_=pos(f['reference'],0)
    for yy in range(top,top+ph,15): d.line([x,yy,x,yy+8],fill=INK,width=2)
    for p in f['players']:
        px,py=pos(p['x'],p['y']); color=INK if p['team']==e['team_id'] else BLUE
        if p['line']: d.ellipse([px-17,py-17,px+17,py+17],outline=AMBER if p['id']==e['highlight_id'] else color,width=4 if p['id']==e['highlight_id'] else 1)
        d.ellipse([px-12,py-12,px+12,py+12],fill=color if p['observed'] else PITCH,outline=color,width=2)
        d.text((px,py),str(p['number']),font=font(12),fill=BG if p['observed'] else color,anchor='mm')
    bx,by=pos(*f['ball']);d.ellipse([bx-6,by-6,bx+6,by+6],fill='white',outline=INK,width=2)
    p=next(p for p in f['players'] if p['id']==e['highlight_id']); gap=f['gaps'][str(p['id'])]
    px,py=pos(p['x'],p['y']);rx,_=pos(p['x']+gap,p['y'])
    if 12<=t<29:
        yy=py-31;d.line([px,yy,rx,yy],fill=AMBER,width=4)
        for xx in [px,rx]:d.line([xx,yy-8,xx,yy+8],fill=AMBER,width=3)
    if t<4:
        text(d,(85,40),"What happens when one defender",47,serif=True)
        text(d,(85,100),"doesn't step up?",47,serif=True)
    elif t<12:
        text(d,(85,45),'First, watch the line step',48,serif=True)
        text(d,(85,117),'Adelaide United · 66:58.5 · replay at 0.76×',25)
    elif t<23:
        text(d,(85,45),'Deeper does not mean stationary',48,serif=True)
        text(d,(85,117),'Same sequence · slow replay, then peak held',25)
    elif t<29:
        text(d,(85,45),'The shape narrows again',48,serif=True)
        text(d,(85,117),'No primary candidate: recovery time is not estimated',25)
    else:
        text(d,(85,45),'One Step Behind',56,serif=True)
        text(d,(85,123),'0 qualifying candidates / 44 held-out steps',30)
    sx=1185
    text(d,(sx,215),'F. Talladira',30,serif=True)
    text(d,(sx,270),f'{abs(gap):.2f} m',58,AMBER)
    text(d,(sx,344),'behind peer median' if gap>=0 else 'ahead of peer median',23)
    if 17<=t<23:
        text(d,(sx,422),'At the peak gap:',24)
        text(d,(sx,465),'Talladira +1.76 m',24)
        text(d,(sx,506),'Peers +2.36 m',24)
        text(d,(sx,563),'Still moving forward',24)
    elif 23<=t<29:
        text(d,(sx,422),f"{f['spread']:.2f} m",40)
        text(d,(sx,476),'whole-line spread',24)
        text(d,(sx,540),'Ends at 1.02 m',24)
    elif t>=29:
        text(d,(sx,422),'Interactive replay',24)
        text(d,(sx,467),'/one-step-behind/',23)
        text(d,(sx,545),'GitHub: prithvi-kaizen',22)
        text(d,(sx,582),'football-analytics',22)
    else:
        text(d,(sx,422),'A depth deviation,',24)
        text(d,(sx,460),'not a tactical error',24)
    text(d,(sx,680),'Solid: detected',21)
    text(d,(sx,715),'Hollow: extrapolated',21)
    text(d,(sx,760),'All 4 line players',21)
    text(d,(sx,793),'detected in this clip',21)
    text(d,(85,175),f"Match clock {f['clock']} · source frame {f['frame']} · tracking: SkillCorner Open Data (MIT)",19)
    return im

def main():
    data=json.loads((ROOT/'outputs/replays.json').read_text());e=next(e for e in data['examples'] if e['id']=='1996435-042')
    target=ROOT/'outputs/demo.mp4'
    command=['ffmpeg','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    with (ROOT/'outputs/video-render.log').open('w') as log:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        for n in range(FPS*DURATION):
            im=frame(n/FPS,e)
            if n in [60,300,600,780,915]: im.save(ROOT/f'outputs/video-frame-{n:03}.png')
            process.stdin.write(im.tobytes())
        process.stdin.close()
        if process.wait()!=0: raise RuntimeError('FFmpeg failed; see video-render.log')
    (ROOT/'outputs/video-manifest.json').write_text(json.dumps(dict(example_id=e['id'],duration_s=DURATION,fps=FPS,size=[W,H],silent=True,
        note='Real 10Hz positions held between samples. Sequence replayed with disclosed slower rates; no interpolation. No primary candidate or candidate recovery claim.',
        timing=[dict(start=0,end=4,story='question; first real frame'),dict(start=4,end=12,story='full real sequence, 0.76x'),dict(start=12,end=23,story='slow replay to 3.53m peak; held peak; real displacements'),dict(start=23,end=29,story='continue to clip end, final spread 1.02m'),dict(start=29,end=32,story='0/44 finding and project route')]),indent=2)+'\n')
    print(target)
if __name__=='__main__':main()
