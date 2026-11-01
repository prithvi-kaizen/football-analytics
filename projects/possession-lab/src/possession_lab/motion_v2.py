"""Continuous, role-based *illustrative* football motion. Legacy generators stay frozen.

A steering model is not an empirically validated football simulator. Passes and
interceptions are scripted, not emergent tactical decisions. Latent geometry is
separate from observation noise, missingness and track-identity failures.
"""
from dataclasses import dataclass, replace

import numpy as np

from .schema import TrackingBatch

FPS = 25
DURATION = 125
ROLES = ('GK', 'LB', 'LCB', 'RCB', 'RB', 'LCM', 'CM', 'RCM', 'LW', 'CF', 'RW')
PLAYER_SPEED_LIMIT = 7.0
PLAYER_ACCEL_LIMIT = 3.0
BALL_SPEED_LIMIT = 35.0
BALL_ACCEL_LIMIT = 35.0
# Control changes occur at a physical reception, not by relocating a carrier.
ROUTE = ((0, 'H', 6), (7, 'H', 7), (14, 'H', 9), (21, 'A', 6),
         (28, 'A', 9), (35, 'A', 7), (52, 'A', 6), (59, 'A', 8),
         (66, 'H', 7), (73, 'H', 9), (80, 'H', 8), (96, 'H', 6),
         (103, 'H', 10), (110, 'A', 7), (117, 'A', 8))
STOPPAGES = ((42, 48), (86, 92))


@dataclass(frozen=True)
class MotionMatch:
    tracking: TrackingBatch
    truth: np.ndarray
    actions: tuple
    diagnostics: dict


def _limit(values, maximum):
    lengths = np.linalg.norm(values, axis=-1, keepdims=True)
    return values * np.minimum(1, maximum / np.maximum(lengths, 1e-12))


def _quintic(p0, p1, v0, v1, a0, a1, count):
    """C2 endpoint conditions match the carrier's actual path on either side."""
    duration = count / FPS
    c0, c1, c2 = p0, v0 * duration, a0 * duration ** 2 / 2
    residual = np.stack((p1-c0-c1-c2, v1*duration-c1-2*c2,
                         a1*duration**2-2*c2))
    tail = np.linalg.solve(np.array([[1., 1., 1.], [3., 4., 5.], [6., 12., 20.]]), residual)
    coefficients = np.vstack((c0, c1, c2, tail))
    s = np.linspace(0, 1, count+1)
    return np.stack([s**k for k in range(6)], axis=1) @ coefficients


def _kinematics(xy):
    velocity = np.diff(xy, axis=0) * FPS
    acceleration = np.diff(xy, n=2, axis=0) * FPS**2
    return float(np.max(np.linalg.norm(velocity, axis=-1))), float(np.max(np.linalg.norm(acceleration, axis=-1)))


def generate(seed=101, mechanism='ordinary'):
    if not isinstance(seed, int) or isinstance(seed, bool) or not 1 <= seed <= 99999:
        raise ValueError('seed must be an integer in 1..99999')
    if mechanism not in ('ordinary', 'stationary_live', 'contested', 'player_gaps', 'identity_switches'):
        raise ValueError('unknown mechanism')
    rng = np.random.default_rng(seed)
    n = FPS * DURATION
    time = np.arange(n) / FPS
    route = tuple(row for row in ROUTE if not (mechanism == 'stationary_live' and row[0] == 14))
    owner, carrier = np.empty(n, dtype='<U1'), np.empty(n, dtype=int)
    for index, (start, side, slot) in enumerate(route):
        stop = route[index+1][0]*FPS if index+1 < len(route) else n
        owner[start*FPS:stop], carrier[start*FPS:stop] = side, slot
    truth = owner.copy()
    for start, stop in STOPPAGES:
        truth[start*FPS:stop*FPS] = 'D'

    anchors_h = np.array([[6,34],[25,9],[23,26],[23,43],[25,59],
                          [43,15],[40,34],[43,53],[62,12],[66,34],[62,56]], float)
    anchors_a = anchors_h.copy()
    anchors_a[:, 0] = 105-anchors_a[:, 0]
    anchors_a[:, 1] = 68-anchors_a[:, 1]
    anchors = np.stack((anchors_h, anchors_a))
    anchors[:, 1:] += rng.normal(0, 1.1, (2,10,2))
    position = anchors.copy()
    velocity = np.zeros_like(position)
    positions = np.empty((n,2,11,2))
    positions[0] = position
    drift = rng.normal(0, .4, (2,11,2))
    # Independent bounded intentions per player, smoothed in time.
    knots = rng.uniform(-3.5,3.5,(int(DURATION/4)+3,2,11,2))
    guide_knots = rng.uniform([38,23],[67,45],(int(DURATION/8)+3,2))
    held = {}
    for i in range(1,n):
        t = time[i]
        k = int(t//4);u = (t%4)/4;u = u*u*(3-2*u)
        intention = (1-u)*knots[k]+u*knots[k+1]
        g = int(t//8);q = (t%8)/8;q = q*q*(3-2*q)
        guide = (1-q)*guide_knots[g]+q*guide_knots[g+1]
        side = 0 if owner[i]=='H' else 1
        slot = carrier[i]
        target = anchors + intention
        target[:,:,0] += .30*(guide[0]-52.5)
        target[:,:,1] += .24*(guide[1]-34)
        target[side,1:,0] += 3 if side==0 else -3
        # A supporting carrier seeks a different patch of space; no position assignment.
        target[side,slot] = guide + intention[side,slot]*.6
        defending = 1-side
        distances = np.linalg.norm(position[defending]-position[side,slot],axis=1)
        distances[0] = np.inf
        presser = int(np.argmin(distances))
        separation = 2.2
        if mechanism=='contested' and 25<=t<29:
            separation = .55
        target[defending,presser] = position[side,slot]+[separation if side else -separation,.4]
        # Other defenders mark nearby opposition while maintaining formation.
        for defender in (2,3):
            opposite = 8 if defender==2 else 10
            target[defending,defender] = .7*target[defending,defender]+.3*(position[side,opposite]+[2 if side else -2,0])
        for team in (0,1):
            target[team,0] = [6 if team==0 else 99,34+.2*(guide[1]-34)]
        for a,b in STOPPAGES:
            if a<=t<b:
                if a not in held:held[a] = position[side,slot].copy()
                target[side,slot] = held[a]
        slow = mechanism=='stationary_live' and 11<=t<19
        if mechanism=='stationary_live' and 12<=t<18:
            if 'live' not in held:held['live'] = position[side,slot].copy()
            target[side,slot] = held['live']
        target = np.clip(target,[3,3],[102,65])
        # Soft avoidance is a steering preference, not collision or contact physics.
        flat = position.reshape(22,2)
        delta = flat[:,None]-flat[None]
        distance = np.linalg.norm(delta,axis=-1)
        np.fill_diagonal(distance,np.inf)
        repulsion = (delta/np.maximum(distance[:,:,None],.15)*np.maximum(0,1.05-distance)[:,:,None]).sum(axis=1).reshape(2,11,2)
        desired = .65*(target-position)+repulsion*.9
        maximum = np.full((2,11,1), .65 if slow else PLAYER_SPEED_LIMIT)
        maximum[:,0] = 2.2
        desired = _limit(desired,maximum)
        acceleration = _limit((desired-velocity)/.55,PLAYER_ACCEL_LIMIT)
        velocity += acceleration/FPS
        position += velocity/FPS
        positions[i] = position
    home, away = positions[:,0], positions[:,1]
    controlled = np.empty((n,2))
    for i in range(n):
        side = 0 if owner[i]=='H' else 1
        controlled[i] = positions[i,side,carrier[i]] + ([.65,.15] if side==0 else [-.65,.15])
    velocities = np.gradient(positions,1/FPS,axis=0)
    accelerations = np.gradient(velocities,1/FPS,axis=0)
    ball = controlled.copy()
    actions = []
    for index,(catch_s,side,slot) in enumerate(route[1:],1):
        catch = catch_s*FPS
        old_side = 0 if route[index-1][1]=='H' else 1
        old_slot = route[index-1][2]
        new_side = 0 if side=='H' else 1
        restart = catch_s in (52,96)
        if restart:
            release = (48 if catch_s==52 else 92)*FPS
            # Filled after the stopping segment below; its start is stationary.
            actions.append({'type':'restart','release':release,'catch':catch,'from_team':side,'from_slot':old_slot,'to_team':side,'to_slot':slot})
            continue
        previous_catch = route[index-1][0]*FPS
        chosen = None
        for duration in (2.,2.4,2.8,3.2,3.8,4.4,5.):
            release = catch-round(duration*FPS)
            if release<=previous_catch+10:continue
            path = _quintic(controlled[release],controlled[catch],velocities[release,old_side,old_slot],
                            velocities[catch,new_side,slot],accelerations[release,old_side,old_slot],
                            accelerations[catch,new_side,slot],catch-release)
            speed,acc = _kinematics(path)
            if speed<=BALL_SPEED_LIMIT and acc<=BALL_ACCEL_LIMIT:
                chosen = release,path
                break
        if chosen is None:raise ValueError('No bounded pass path for seed '+str(seed))
        release,path=chosen;ball[release:catch+1] = path
        actions.append({'type':'pass' if route[index-1][1]==side else 'interception','release':release,'catch':catch,'from_team':route[index-1][1],'from_slot':old_slot,'to_team':side,'to_slot':slot})
    for a,b in STOPPAGES:
        start,stop,settle=a*FPS,b*FPS,(a+2)*FPS
        side = 0 if owner[start]=='H' else 1;slot=carrier[start]
        rest = controlled[stop].copy()
        ball[start:settle+1] = _quintic(controlled[start],rest,velocities[start,side,slot],np.zeros(2),accelerations[start,side,slot],np.zeros(2),settle-start)
        ball[settle:stop+1] = rest
        event=next(e for e in actions if e['type']=='restart' and e['release']==stop)
        catch=event['catch'];new_side=0 if event['to_team']=='H' else 1;new_slot=event['to_slot']
        ball[stop:catch+1] = _quintic(rest,controlled[catch],np.zeros(2),velocities[catch,new_side,new_slot],np.zeros(2),accelerations[catch,new_side,new_slot],catch-stop)
    if mechanism=='stationary_live':
        start,settle,resume=12*FPS,14*FPS,18*FPS
        side=0;slot=carrier[start];rest=controlled[resume].copy()
        ball[start:settle+1]=_quintic(controlled[start],rest,velocities[start,side,slot],np.zeros(2),accelerations[start,side,slot],np.zeros(2),settle-start)
        ball[settle:resume+1]=rest
    player_speed,player_acc = _kinematics(positions)
    ball_speed,ball_acc = _kinematics(ball)
    diagnostics = {'player_max_speed_mps':player_speed,'player_max_acceleration_mps2':player_acc,
                   'ball_max_speed_mps':ball_speed,'ball_max_acceleration_mps2':ball_acc,
                   'max_player_step_m':player_speed/FPS,'limits':{'player_speed':PLAYER_SPEED_LIMIT,'player_acceleration':PLAYER_ACCEL_LIMIT,'ball_speed':BALL_SPEED_LIMIT,'ball_acceleration':BALL_ACCEL_LIMIT}}
    if not (player_speed<=PLAYER_SPEED_LIMIT+1e-8 and player_acc<=PLAYER_ACCEL_LIMIT+1e-8
            and ball_speed<=BALL_SPEED_LIMIT+1e-6 and ball_acc<=BALL_ACCEL_LIMIT+1e-6):
        raise ValueError('Latent motion limit failed: '+str(diagnostics))
    if np.min(positions)<0 or np.max(positions[:,:,:,0])>105 or np.max(positions[:,:,:,1])>68:
        raise ValueError('Player left physical pitch')
    provenance={'kind':'synthetic','generator':'role_motion_v2','seed':seed,'mechanism':mechanism,
                'scope':'Scripted continuous illustrative possession sequence, not a calibrated football simulator',
                'roles':list(ROLES),'kinematics':diagnostics}
    batch=TrackingBatch(np.arange(n),time,np.ones(n,int),ball,home,away,provenance=provenance)
    return MotionMatch(batch,truth,tuple(actions),diagnostics)


def observe(match,seed=101,noise=.12,loss=.05,gap_start=12.,gap_duration=6.,mechanism='ordinary'):
    """Imperfections are measurements; the latent world and possession truth stay fixed."""
    rng=np.random.default_rng(np.random.SeedSequence([seed,7001]))
    batch=match.tracking
    ball,home,away=[value.copy() for value in (batch.ball,batch.home,batch.away)]
    for array in (ball,home,away):array+=rng.normal(0,noise,array.shape)
    missing=rng.random(len(ball))<loss
    start=round(gap_start*batch.fps);stop=min(len(ball),start+round(gap_duration*batch.fps))
    missing[start:stop]=True;ball[missing]=np.nan
    if mechanism=='player_gaps':
        for team in (home,away):
            for slot in range(team.shape[1]):
                a=int(rng.integers(0,max(1,len(ball)-100)));team[a:a+75,slot]=np.nan
    if mechanism=='identity_switches':
        for team in (home,away):
            for a in range(250,len(ball),500):
                team[a:, [2,3]]=team[a:, [3,2]]
    provenance={**batch.provenance,'observation':{'seed':seed,'noise_m':noise,'random_ball_loss':loss,
                 'gap_start_frame':start,'gap_stop_frame':stop,'mechanism':mechanism},
                 'kinematic_limits_apply_to':'latent paths before measurement noise or identity swaps'}
    return replace(batch,ball=ball,home=home,away=away,provenance=provenance)
