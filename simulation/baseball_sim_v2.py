"""
야구 게임 밸런스 시뮬레이터 v2 ① 뼈대 (공 하나씩 계산)
- 자동 경기는 공 하나씩 정하면서 중계 화면으로 보여줌 (기획 문서 3.4절). 이 파일은 그 계산 규칙.
- ① 뼈대: 볼카운트 싸움만 (존 안/밖 → 스윙 → 맞힘 → 파울/인플레이). v1과 같은 결과가 나오는지 확인하는 단계.
- 아직 없는 것: ② 빠진 공(실투·폭투·사구 위치) ③ 구종·구종 등급 ④ 도루·견제 ⑤ 실책·병살·희생플라이 ⑥ 체력(투구 수)
- 공 하나의 모양은 MLB 2025 Statcast 볼카운트별 자료 (KBO 공 단위 자료는 못 구함),
  최종 결과(삼진·볼넷·홈런·BABIP)는 v1 기준값(KBO 범위 안)에 맞춤. docs/research/league-average.md 4·6장.
- 선수·팀·경기 진행(주자 진루, 투수 교체)은 v1 것을 그대로 씀.
"""
import math
import random

import baseball_sim as v1
from baseball_sim import Batter, Pitcher, make_team, slash

# ------------------------------------------------------------
# 1. 공 하나의 기준 (MLB 2025 정규시즌, 볼카운트별)
# ------------------------------------------------------------
# (볼, 스트라이크): (존 안 비율, 존 안 스윙, 존 밖 스윙, 존 안 맞힘, 존 밖 맞힘)
COUNT_BASE = {
    (0, 0): (0.550, 0.451, 0.162, 0.829, 0.514),
    (0, 1): (0.460, 0.738, 0.281, 0.837, 0.533),
    (0, 2): (0.324, 0.867, 0.324, 0.862, 0.586),
    (1, 0): (0.562, 0.591, 0.219, 0.833, 0.527),
    (1, 1): (0.511, 0.772, 0.310, 0.842, 0.556),
    (1, 2): (0.384, 0.883, 0.376, 0.860, 0.606),
    (2, 0): (0.601, 0.553, 0.192, 0.851, 0.564),
    (2, 1): (0.578, 0.778, 0.317, 0.853, 0.575),
    (2, 2): (0.475, 0.887, 0.420, 0.870, 0.624),
    (3, 0): (0.628, 0.114, 0.030, 0.858, 0.658),
    (3, 1): (0.627, 0.709, 0.256, 0.869, 0.634),
    (3, 2): (0.598, 0.886, 0.437, 0.884, 0.662),
}
TAKE_STRIKE = {True: 0.876, False: 0.045}  # 그냥 본 공이 스트라이크 판정 (존 안 / 존 밖)
FOUL_SHARE = {True: 0.499, False: 0.599}   # 맞힌 공 중 파울 (존 안 / 존 밖)
HBP_TAKE_OUT = 0.0077                       # 존 밖 공을 그냥 봤을 때 사구 (MLB 2025: 존 밖 공의 0.55%)
# 인플레이 타구의 질: 존 밖 공을 맞히면 약함 (MLB 2025 인플레이 홈런 존 안 5.1%·존 밖 1.8%, BABIP .296·.266)
ZONE_HIT = {True: {"hr": 0.13, "babip": 0.024}, False: {"hr": -0.96, "babip": -0.12}}

# ------------------------------------------------------------
# 2. 맞추기 값 (평균 타자 vs 평균 투수가 v1 기준값과 같은 결과를 내게. calibrate()로 구함)
#    목표: 삼진 18.0%, 볼넷 9.0%, 사구 1.2%, 홈런/컨택 3.0%, BABIP .305 (v1 BASE)
# ------------------------------------------------------------
#    contact +0.417: MLB 공 모양 그대로면 삼진이 많아서(MLB 2025 약 22%) 맞힘을 올려 v1·KBO 범위에 맞춤
SHIFT = {"zone": -0.03, "contact": 0.417, "hr": -0.004, "babip": 0.0, "hbp": 0.108}

# ------------------------------------------------------------
# 3. 능력치가 공 하나에 주는 영향 (능력치 10 차이당 로짓 이동, v1처럼 SCALE을 곱함)
#    v1 역할을 공 하나 단위로 옮김:
#    선구 = 존 밖 공에 덜 스윙 / 정확 = 헛스윙이 적음 / 구속 = 헛스윙을 늘림 / 제구 = 존에 더 많이
#    파워·구위·변화·주루·수비 = 인플레이 타구의 질 (v1 가중치 그대로)
# ------------------------------------------------------------
W2 = {
    "zone":    {"ctl": 0.18},
    "zswing":  {"eye": -0.15},   # 선구가 높으면 존 안 공도 조금 더 골라서 봄 (스윙 전체가 줄어 볼넷 쪽으로)
    "oswing":  {"eye": -0.40},
    "contact": {"con": 0.55, "vel": -0.35, "brk": -0.08, "stuff": -0.05},
    "hr":      v1.W["hr"],
    "babip":   v1.W["babip"],
    "double":  v1.W["double"],
    "triple":  v1.W["triple"],
}
SCALE = v1.SCALE


def logit(p):
    return math.log(p / (1 - p))


def inv_logit(x):
    return 1 / (1 + math.exp(-x))


def _ability(kind, v):
    return SCALE * sum(w * (v[k] - 50) / 10 for k, w in W2[kind].items())


def _p(base, kind, v, extra=0.0):
    return inv_logit(logit(base) + SHIFT.get(kind, 0.0) + extra + _ability(kind, v))


def _in_play(v, in_zone, rng):
    """인플레이 타구 결과 (v1 2·3단계와 같은 방식, 존 안/밖에 따라 타구 질만 다름)"""
    z = ZONE_HIT[in_zone]
    if rng.random() < _p(v1.BASE["hr_contact"], "hr", v, z["hr"]):
        return "HR"
    if rng.random() < _p(v1.BASE["babip"], "babip", v, z["babip"]):
        r = rng.random()
        p3 = inv_logit(logit(v1.BASE["triple"]) + _ability("triple", v))
        p2 = inv_logit(logit(v1.BASE["double"]) + _ability("double", v))
        if r < p3:
            return "3B"
        if r < p3 + p2:
            return "2B"
        return "1B"
    return "OUT"


def plate_appearance(b: Batter, p: Pitcher, defense, rng=random, log=None):
    """공 하나씩 던져서 타석 결과를 냄. log에 리스트를 넘기면 공마다 결과를 적음."""
    balls = strikes = 0
    while True:
        p.pitches_today += 1
        f = p.fatigue_factor()
        v = {"con": b.con, "pow": b.pow, "eye": b.eye, "spd": b.spd, "defense": defense,
             "vel": p.vel - f, "stuff": p.stuff - f, "ctl": p.ctl - f, "brk": p.brk - f}
        zone, zsw, osw, zcon, ocon = COUNT_BASE[(balls, strikes)]
        in_zone = rng.random() < _p(zone, "zone", v)
        swing = rng.random() < (_p(zsw, "zswing", v) if in_zone else _p(osw, "oswing", v))
        if swing:
            if rng.random() < _p(zcon if in_zone else ocon, "contact", v):
                if rng.random() < FOUL_SHARE[in_zone]:
                    pitch = "파울"
                    if strikes < 2:
                        strikes += 1
                else:
                    res = _in_play(v, in_zone, rng)
                    if log is not None:
                        log.append(("인플레이", res))
                    return res
            else:
                pitch = "헛스윙"
                strikes += 1
        else:
            if not in_zone and rng.random() < inv_logit(logit(HBP_TAKE_OUT) + SHIFT["hbp"]):
                if log is not None:
                    log.append(("사구", "HBP"))
                return "HBP"
            if rng.random() < TAKE_STRIKE[in_zone]:
                pitch = "스트라이크"
                strikes += 1
            else:
                pitch = "볼"
                balls += 1
        if log is not None:
            log.append((pitch, "삼진" if strikes == 3 else "볼넷" if balls == 4 else f"{balls}-{strikes}"))
        if strikes == 3:
            return "K"
        if balls == 4:
            return "BB"


# ------------------------------------------------------------
# 4. 맞추기와 실험
# ------------------------------------------------------------
def pa_stats(b, p, n, rng, defense=50):
    st, pitches, kinds = {}, 0, {}
    for _ in range(n):
        p.pitches_today = 0
        log = []
        r = plate_appearance(b, p, defense, rng, log)
        st[r] = st.get(r, 0) + 1
        pitches += p.pitches_today
        for k, _ in log:
            kinds[k] = kinds.get(k, 0) + 1
    st["PA"] = n
    return st, pitches, kinds


def calibrate(n=200_000, rounds=8, seed=11):
    """평균 타자 vs 평균 투수가 v1 기준값을 내도록 SHIFT를 맞춤 (결과를 SHIFT에 적어 둠)"""
    rng = random.Random(seed)
    b = Batter("B", 50, 50, 50, 50, 50, 50)
    p = Pitcher("P", 50, 50, 50, 50, 10**9)
    for _ in range(rounds):
        st, _, _ = pa_stats(b, p, n, rng)
        pa = st["PA"]
        k, bb, hbp = st.get("K", 0) / pa, st.get("BB", 0) / pa, st.get("HBP", 0) / pa
        contact = pa - st.get("K", 0) - st.get("BB", 0) - st.get("HBP", 0)
        hr = st.get("HR", 0) / contact
        hits = sum(st.get(x, 0) for x in ("1B", "2B", "3B"))
        babip = hits / (contact - st.get("HR", 0))
        SHIFT["contact"] += 0.8 * (logit(k) - logit(v1.BASE["k"]))
        SHIFT["zone"] += 0.8 * (logit(bb) - logit(v1.BASE["bb"]))
        SHIFT["hbp"] -= logit(hbp) - logit(v1.BASE["hbp"])
        SHIFT["hr"] -= logit(hr) - logit(v1.BASE["hr_contact"])
        SHIFT["babip"] -= logit(babip) - logit(v1.BASE["babip"])
    return {k: round(x, 3) for k, x in SHIFT.items()}


def sensitivity(n=100_000, seed=2):
    """능력치 하나를 50 → 70으로 올렸을 때 기록 변화 (타자 4개, 투수 4개)"""
    rng = random.Random(seed)
    rows = {}
    for who, stat in [("기준", None), ("타자", "con"), ("타자", "pow"), ("타자", "eye"), ("타자", "spd"),
                      ("투수", "vel"), ("투수", "stuff"), ("투수", "ctl"), ("투수", "brk")]:
        b = Batter("B", 50, 50, 50, 50, 50, 50)
        p = Pitcher("P", 50, 50, 50, 50, 10**9)
        if stat:
            setattr(b if who == "타자" else p, stat, 70)
        st, pitches, _ = pa_stats(b, p, n, rng)
        s = slash(st)
        s["P/PA"] = pitches / n
        rows[stat or "기준"] = s
    return rows


def league_average(seasons=3, seed=1, pa=None):
    """평균 50짜리 10팀으로 시즌을 돌린 리그 평균 (pa=None이면 v2)"""
    rng = random.Random(seed)
    stats = {}
    for _ in range(seasons):
        teams = [make_team(f"T{i}", 50, rng=rng) for i in range(10)]
        v1.play_season(teams, rng=rng, stats=stats, pa=pa or plate_appearance)
    s = slash(stats)
    s["R/G(팀)"] = stats["R"] / stats["G"] / 2
    return s


def difficulty(scale=0.35, my_offsets=(0, 5, 10, 15), spread=5, trials=5, seed=5):
    """v1 exp5와 같은 실험 (영향력 배율별 내 팀 승률, 1위-꼴찌 승률 차)"""
    global SCALE
    old_v1, old = v1.SCALE, SCALE
    v1.SCALE = SCALE = scale
    try:
        rng = random.Random(seed)
        out, gaps = {}, []
        for off in my_offsets:
            wps = []
            for _ in range(trials):
                offsets = [(-spread + 2 * spread * i / 8) for i in range(9)]
                teams = [make_team("ME", 50 + off, rng=rng)] + [make_team(f"AI{i}", 50 + o, rng=rng) for i, o in enumerate(offsets)]
                standings = v1.play_season(teams, rng=rng, pa=plate_appearance)
                me = next(t for t in teams if t.name == "ME")
                wps.append(me.wins / (me.wins + me.losses))
                if off == 0:
                    wp = [t.wins / (t.wins + t.losses) for t in standings]
                    gaps.append(wp[0] - wp[-1])
            out[off] = sum(wps) / len(wps)
    finally:
        v1.SCALE, SCALE = old_v1, old
    return out, sum(gaps) / len(gaps)


if __name__ == "__main__":
    print("== v2 ① 뼈대: 리그 평균 (평균 50 팀 10개, 3시즌) — v1과 비교 ==")
    a, b = v1.exp1_league_average(), league_average()
    for k in a:
        print(f"  {k:8s} v1 {a[k]:.3f}   v2 {b[k]:.3f}")

    print("\n== 능력치 하나를 50→70 (영향력 배율 1.0, 기획 문서 5.2절과 같은 조건) ==")
    SCALE = 1.0
    for k, s in sensitivity().items():
        print(f"  {k:6s} AVG {s['AVG']:.3f}  OBP {s['OBP']:.3f}  SLG {s['SLG']:.3f}  K% {s['K%']:.3f}  BB% {s['BB%']:.3f}  HR% {s['HR%']:.4f}  타석당 투구 {s['P/PA']:.2f}")
    SCALE = v1.SCALE

    print("\n== 난이도 (영향력 배율 0.35, AI 50±5, 5시즌 평균) ==")
    out, gap = difficulty()
    print("  " + ", ".join(f"+{k}: {v:.3f}" for k, v in out.items()) + f", 1위-꼴찌 차 {gap:.3f}")
