"""한 타석 (1단계: 주자 없이). 5.5절 계산 순서 그대로."""
from config import P, ZX, ZZ, BODY_Z, GROUND_Z
import pitcher_ai
import batter_ai
import judge as jd
import batted_ball as bb


def plate_appearance(batter, pitcher, fielder_dfn, rng, log=None, wp_cb=None):
    """결과와 타구(속도, 각도, 방향)를 돌려줌. fielder_dfn: 숫자 또는 (각도, 방향) → 수비 능력치 함수.
    wp_cb: 주자가 있을 때 바닥으로 빠진 공이 폭투가 되면 부르는 함수 (2단계)."""
    balls = strikes = 0
    while True:
        count = (balls, strikes)
        pitch = pitcher_ai.choose_pitch(pitcher, count, rng)
        tx, tz, aim = pitcher_ai.choose_target(pitch, count, rng)
        x, z, kind = pitcher_ai.locate(pitcher, pitch, (tx, tz), rng)
        pitcher.pitches_today += 1
        in_zone = abs(x) <= ZX and abs(z) <= ZZ
        if log is not None:
            log["pitches"] += 1
            log["zone"] += in_zone
        # 사구: 몸에 닿는 위치 (스윙과 상관없이 먼저 판정)
        if x < P["body_x"] and abs(z) < BODY_Z:
            return "사구", None
        if wp_cb is not None and z < GROUND_Z and rng.random() < P["wp_prob"]:
            wp_cb()
        swing = batter_ai.decide_swing(batter, pitcher, pitch, x, z, count, rng)
        if log is not None:
            log["swing_in" if in_zone else "swing_out"] += swing
        if not swing:
            if in_zone:          # ABS: 존 안 = 무조건 스트라이크
                strikes += 1
                if strikes == 3:
                    return "삼진", None
            else:
                balls += 1
                if balls == 4:
                    return "볼넷", None
            continue
        t = batter_ai.timing(batter, pitcher, pitch, count, rng)
        tg = batter_ai.timing_grade(t)
        stype = batter_ai.choose_swing_type(pitcher, x, z, count, rng)
        comp = batter_ai.compat(stype, x, z)
        q = jd.quality(batter, pitcher, tg, comp, x, z)
        res = jd.judge(q, tg, rng, strikes)
        if log is not None:
            log[("w" if res == "헛스윙" else ("f" if res == "파울" else "b")) + ("_in" if in_zone else "_out")] += 1
        if res == "헛스윙":
            strikes += 1
            if strikes == 3:
                return "삼진", None
        elif res == "파울":
            if strikes < 2:
                strikes += 1
        else:
            ev, la, d = bb.make_ball(batter, pitcher, q, stype, x, z, t, rng)
            if log is not None:
                log["ev"] += ev
                log["la"] += la
                log["dir%d" % d] += 1
                log["hard"] += ev >= 95
            dfn = fielder_dfn(la, d) if callable(fielder_dfn) else fielder_dfn
            return bb.result(batter, pitcher, dfn, ev, la, d, rng), (ev, la, d)
