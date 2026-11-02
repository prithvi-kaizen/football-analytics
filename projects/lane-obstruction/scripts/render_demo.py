"""Render a 30-second, silent MP4 using executed replay/results and Pillow + FFmpeg."""
import json
from pathlib import Path
import shutil
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPLAY = json.loads((ROOT/'outputs/replays.json').read_text())
RESULTS = json.loads((ROOT/'outputs/results.json').read_text())
EX = REPLAY['examples'][0]
PAPER, INK, MUTED, TEAL, RUST, FIELD = '#f7f4ec', '#192724', '#4c5955', '#00665c', '#973c20', '#e5ede4'


def font(size, heading=False):
    candidates = ['/System/Library/Fonts/Supplemental/Georgia.ttf' if heading else '/System/Library/Fonts/Supplemental/Arial.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf' if heading else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def wrapped(draw, text, x, y, width=39, size=23, fill=INK):
    for line in textwrap.wrap(text, width=width):
        draw.text((x,y), line, font=font(size), fill=fill)
        y += size+9
    return y


def result_figure():
    image = Image.new('RGB', (1280,720), PAPER)
    d = ImageDraw.Draw(image)
    d.text((50,35), 'The simpler geometry had stronger agreement', fill=INK, font=font(42, True))
    d.text((50,95), '832 labelled starts | two pipeline-held-out A-League matches', fill=MUTED, font=font(24))
    d.text((50,140), 'Arrival rho minus geometry rho; paired phase-bootstrap 95% intervals', fill=MUTED, font=font(22))
    x = lambda v: 410+(v+.5)/.6*760
    d.line((x(0),200,x(0),475), fill=MUTED, width=2)
    entries = list(RESULTS['per_match'].items())+[('Pooled',RESULTS['pooled'])]
    for i, (name,v) in enumerate(entries):
        y = 230+i*95
        d.text((60,y-17),name,fill=INK,font=font(26))
        lo,hi=v['interval_95']
        d.line((x(lo),y,x(hi),y),fill=RUST,width=5)
        d.ellipse((x(v['delta_rho'])-7,y-7,x(v['delta_rho'])+7,y+7),fill=RUST)
        d.text((x(v['delta_rho'])-42,y+14), f'{v["delta_rho"]:+.3f}',fill=INK,font=font(22))
    for v in [-.5,-.3,-.1,0,.1]:
        d.text((x(v)-20,505),f'{v:.1f}',fill=INK,font=font(22))
    d.text((50,565),'Geometry rho 0.293 | arrival rho 0.062 | improvement hypothesis not supported', fill=INK, font=font(26))
    d.text((50,610),'Dependent provider categories, not independent ground truth. No prevented-pass claim.', fill=MUTED, font=font(23))
    d.text((50,667),'Data: SkillCorner Open Data, with PySport. Intervals condition on these two matches.', fill=MUTED, font=font(20))
    return image


def render(second):
    if second >= 27:
        return result_figure()
    image = Image.new('RGB',(1280,720),PAPER);d=ImageDraw.Draw(image)
    d.text((35,24),'The Defender Nobody Notices',font=font(46,True),fill=INK)
    d.text((35,87),'A lane-obstruction proxy, not validated prevented passes',font=font(25),fill=MUTED)
    f = EX['frames'][max(0,min(len(EX['frames'])-1,int(max(0,second-3)/24*len(EX['frames']))))]
    def point(p):
        return (35+(p[0]+REPLAY['length']/2)*720/REPLAY['length'],150+(REPLAY['width']/2-p[1])*470/REPLAY['width'])
    d.rectangle((35,150,755,620),fill=FIELD,outline=MUTED,width=2)
    d.line((395,150,395,620),fill=MUTED,width=1)
    d.ellipse((332,322,458,448),outline=MUTED,width=1)
    for left in [35,755-16.5*720/REPLAY['length']]:
        d.rectangle((left,385-20.16*470/REPLAY['width'],left+16.5*720/REPLAY['length'],385+20.16*470/REPLAY['width']),outline=MUTED,width=1)
    j=0;target=f['xy'][EX['ids'].index(EX['target_ids'][j])];ball=f['ball']
    # The first chronological example and first target are fixed, never chosen for score.
    d.line((*point(ball),*point(target)),fill=RUST,width=5)
    for i,pid in enumerate(EX['ids']):
        x,y=point(f['xy'][i]);attack=EX['teams'][i]==EX['attacking_team'];c=TEAL if attack else RUST
        box=(x-8,y-8,x+8,y+8)
        if attack:d.ellipse(box,fill=PAPER,outline=c,width=2)
        else:d.rectangle(box,fill=PAPER,outline=c,width=2)
        if not f['detected'][i]:
            d.line((x-9,y+11,x+9,y+11),fill=c,width=1)
    x,y=point(ball);d.ellipse((x-4,y-4,x+4,y+4),fill=INK)
    x,y=point(target);d.ellipse((x-14,y-14,x+14,y+14),outline=INK,width=2)
    d.text((790,150),f'Target: {EX["target_names"][j]}',font=font(26),fill=INK)
    d.text((790,195),f'Tracking time +{f["t"]:.1f} s',font=font(23),fill=INK)
    d.text((790,237),f'Lane availability {1-f["obstruction"][j]:.3f}',font=font(28),fill=TEAL)
    d.text((790,280),f'Geometry {1-f["geometry"][j]:.0f} | frozen {1-f["frozen_obstruction"][j]:.3f}',font=font(23),fill=MUTED)
    message = 'What happens to a passing lane before anyone tries the pass?' if second < 3 else 'Compare the current lane with the same ball and target but frozen defender states.' if second < 16 else 'Positions can obstruct a route. These scores do not establish that a pass was prevented.'
    wrapped(d,message,790,338,width=31,size=24)
    d.text((790,518),'Availability = 1 - obstruction',font=font(21),fill=MUTED)
    d.text((790,552),f'{sum(f["detected"])}/22 players detected',font=font(21),fill=MUTED)
    d.text((790,584),'Other positions are extrapolated',font=font(21),fill=MUTED)
    # Compact timeline shares the same 0–1 scale for current and frozen states.
    tx=lambda t: 55+t/EX['frames'][-1]['t']*680
    ty=lambda v: 674-v*38
    for key,c in [('frozen_obstruction',RUST),('obstruction',TEAL)]:
        pts=[(tx(fr['t']),ty(1-fr[key][j])) for fr in EX['frames']]
        if key == 'frozen_obstruction':
            for a,b in zip(pts,pts[1:]):
                for step in range(0,10,2):
                    q=lambda s:(a[0]+(b[0]-a[0])*s,a[1]+(b[1]-a[1])*s)
                    d.line([q(step/10),q((step+1)/10)],fill=c,width=3)
        else:
            d.line(pts,fill=c,width=3)
    d.line((tx(f['t']),630,tx(f['t']),680),fill=INK,width=1)
    d.text((10,630),'1',font=font(15),fill=MUTED)
    d.text((10,663),'0',font=font(15),fill=MUTED)
    d.text((790,630),'Solid: current; dashed: frozen',font=font(21),fill=MUTED)
    d.text((790,660),'Timeline scale: 0-1 availability',font=font(21),fill=MUTED)
    d.text((35,692),'SkillCorner Open Data + PySport | 3.5 s sampled at 2 Hz, slowed | underlines: extrapolated',font=font(17),fill=MUTED)
    return image


if __name__ == '__main__':
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise SystemExit('Install open-source FFmpeg to render the MP4; Python outputs remain usable.')
    result_figure().save(ROOT/'outputs/results.png')
    render(15).save(ROOT/'outputs/demo-poster.png')
    command=[ffmpeg,'-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','12','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'outputs/demo.mp4')]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as process:
        for frame in range(30*12):
            process.stdin.write(render(frame/12).tobytes())
        process.stdin.close()
        if process.wait():
            raise RuntimeError('FFmpeg render failed')
    print('Rendered 30-second outputs/demo.mp4, poster and results figure')
