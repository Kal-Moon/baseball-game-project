"""
야구 게임 밸런스 시뮬레이터 v2 (공 하나씩 계산)
- 자동 경기는 공 하나씩 정하면서 중계 화면으로 보여줌 (기획 문서 3.4절). 이 파일은 그 계산 규칙.
- 만드는 순서 (기획 문서 5.4·5.5절):
  ① 뼈대: 볼카운트 싸움 (존 안/밖 → 스윙 → 맞힘 → 파울/인플레이)  — 2026-10-08
  ② 실투: 한가운데 실투 / 빠진 공(몸쪽 = 사구, 바닥 = 주자 있을 때 낮은 확률로 폭투)  — 2026-10-08
  ③ 구종·구종 등급 ④ 도루·견제 ⑤ 실책·병살·희생플라이 ⑥ 체력(투구 수)  — 아직
- 공 하나의 모양은 MLB 2025 Statcast 자료 (KBO 공 단위 자료는 못 구함),
  최종 결과(삼진·볼넷·홈런·BABIP)는 v1 기준값(KBO 범위 안), 사구는 KBO 2025에 맞춤. docs/research/league-average.md 4·6·7장.
- 선수·팀·주자 진루·투수 교체는 v1 것을 그대로 씀.
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
# 인플레이 타구의 질: 존 밖 공을 맞히면 약함 (MLB 2025 인플레이 홈런 존 안 5.1%·존 밖 1.8%, BABIP .296·.266)
ZONE_HIT = {True: {"hr": 0.13, "babip": 0.024}, False: {"hr": -0.96, "babip": -0.12}}

# ------------------------------------------------------------
# 1-2. ② 실투 (기획 문서 3.1절 "실투의 종류", "몸에 맞는 공(사구)")
#   실투 = 한가운데 실투(대부분) / 빠진 공(적게). ★ = 근거 없이 정한 시뮬레이션 값
# ------------------------------------------------------------
MISTAKE_RATE = 0.04   # ★ 실투 / 공 (제구 50). 제구가 낮을수록 많음 (W2["mistake"])
MIDDLE_SHARE = 0.70   # ★ 실투 중 한가운데 실투 비중 ("대부분")
# 한가운데 실투: 존 안 다른 칸보다 치기 쉬움 (MLB 2025 5번 칸 vs 존 안 나머지 칸, 로짓 차)
#   스윙 76.3% vs 65.2%, 맞힘 90.1% vs 83.8%, 인플레이 홈런 6.9% vs 4.7%, BABIP .306 vs .294
MIDDLE = {"swing": 0.54, "contact": 0.57, "hr": 0.41, "babip": 0.06, "take_strike": 0.98}  # take_strike ★
# 빠진 공: 존에서 크게 벗어남 → 거의 확실한 볼
WILD = {"swing": 0.05, "contact": 0.30}          # ★ 빠진 공에 스윙·맞힘 (거의 안 침)
WILD_DIR = {"body": 0.25, "low": 0.40}           # ★ 빠진 공이 가는 곳: 몸쪽(사구) / 바닥 / 나머지(바깥·위, 볼)
WP_RATE = 0.25                                   # ★ 주자가 있을 때 바닥으로 빠진 공이 폭투가 되는 확률

# ------------------------------------------------------------
# 2. 맞추기 값 (평균 타자 vs 평균 투수가 목표 결과를 내게. calibrate()로 구함)
#    목표: 삼진 18.0%, 볼넷 9.0%, 홈런/컨택 3.0%, BABIP .305 (v1 BASE), 사구 1.44% (KBO 2025, 3.1절)
#    contact +: MLB 공 모양 그대로면 삼진이 많아서(MLB 2025 약 22%) 맞힘을 올려 v1·KBO 범위에 맞춤
#    body: 빠진 공 중 몸쪽 비율(WILD_DIR["body"])을 사구 목표에 맞춤
# ------------------------------------------------------------
SHIFT = {"zone": -0.048, "contact": 0.363, "hr": 0.0, "babip": -0.018, "body": 0.412}
TARGET = {"k": 0.180, "bb": 0.090, "hbp": 0.0144, "hr_contact": 0.030, "babip": 0.305}

# ------------------------------------------------------------
# 3. 능력치가 공 하나에 주는 영향 (능력치 10 차이당 로짓 이동, v1처럼 SCALE을 곱함)
#    v1 역할을 공 하나 단위로 옮김:
#    선구 = 존 밖 공에 덜 스윙 / 정확 = 헛스윙이 적음 / 구속 = 헛스윙을 늘림
#    제구 = 존에 더 많이 + 실투가 적음 + 존 안 공이 구석에 붙음
#          (v1의 "제구가 홈런을 조금 줄임"은 실투·구석으로 옮겨서 hr에서 뺌)
#    파워·구위·변화·주루·수비 = 인플레이 타구의 질 (v1 가중치 그대로)
# ------------------------------------------------------------
W2 = {
    "zone":    {"ctl": 0.18},
    "mistake": {"ctl": -0.60},
    "edge_hr": {"ctl": -0.10},
    "zswing":  {"eye": -0.15},   # 선구가 높으면 존 안 공도 조금 더 골라서 봄 (스윙 전체가 줄어 볼넷 쪽으로)
    "oswing":  {"eye": -0.40},
    "contact": {"con": 0.55, "vel": -0.35, "brk": -0.08, "stuff": -0.05},
    "hr":      {k: w for k, w in v1.W["hr"].items() if k != "ctl"},
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
    if kind not in W2:
        return 0.0
    return SCALE * sum(w * (v[k] - 50) / 10 for k, w in W2[kind].items())


def _p(base, kind, v, extra=0.0):
    return inv_logit(logit(base) + SHIFT.get(kind, 0.0) + extra + _ability(kind, v))


def _in_play(v, in_zone, middle, rng):
    """인플레이 타구 결과 (v1 2·3단계와 같은 방식, 존 안/밖·한가운데 실투에 따라 타구 질만 다름)"""
    z = ZONE_HIT[in_zone]
    hr_x = z["hr"] + (MIDDLE["hr"] if middle else 0.0)
    babip_x = z["babip"] + (MIDDLE["babip"] if middle else 0.0)
    if in_zone and not middle:  # 제구가 높으면 존 안 공이 노린 구석에 붙어서 타구가 약함 (직접 플레이의 작은 원과 같은 뜻)
        hr_x += _ability("edge_hr", v)
    if rng.random() < _p(v1.BASE["hr_contact"], "hr", v, hr_x):
        return "HR"
    if rng.random() < _p(v1.BASE["babip"], "babip", v, babip_x):
        r = rng.random()
        p3 = inv_logit(logit(v1.BASE["triple"]) + _ability("triple", v))
        p2 = inv_logit(logit(v1.BASE["double"]) + _ability("double", v))
        if r < p3:
            return "3B"
        if r < p3 + p2:
            return "2B"
        return "1B"
    return "OUT"


def _wild_pitch(ctx):
    """폭투: 모든 주자가 한 베이스씩 (3루 주자는 득점)"""
    b1, b2, b3 = ctx["bases"]
    ctx["runs"] += b3 is not None
    ctx["bases"] = [None, b1, b2]
    ctx["stats"]["WP"] = ctx["stats"].get("WP", 0) + 1


def plate_appearance(b: Batter, p: Pitcher, defense, rng=random, log=None, ctx=None):
    """공 하나씩 던져서 타석 결과를 냄.
    log: 리스트를 넘기면 공마다 (공 종류, 결과)를 적음.
    ctx: {"bases": [1루, 2루, 3루], "runs": 0, "stats": {}} 를 넘기면 폭투로 주자가 움직임 (없으면 주자 없음)."""
    balls = strikes = 0
    while True:
        p.pitches_today += 1
        f = p.fatigue_factor()
        v = {"con": b.con, "pow": b.pow, "eye": b.eye, "spd": b.spd, "defense": defense,
             "vel": p.vel - f, "stuff": p.stuff - f, "ctl": p.ctl - f, "brk": p.brk - f}
        zone, zsw, osw, zcon, ocon = COUNT_BASE[(balls, strikes)]
        st = ctx["stats"] if ctx else {}

        # 던지기: 보통 공 / 한가운데 실투 / 빠진 공
        r, pm = rng.random(), _p(MISTAKE_RATE, "mistake", v)
        kind, wild_dir = "보통", None
        if r < pm * MIDDLE_SHARE:
            kind, in_zone = "한가운데 실투", True
        elif r < pm:
            kind, in_zone = "빠진 공", False
            d = rng.random()
            body = inv_logit(logit(WILD_DIR["body"]) + SHIFT["body"])
            wild_dir = "몸쪽" if d < body else "바닥" if d < body + WILD_DIR["low"] else "바깥·위"
        else:
            in_zone = rng.random() < _p(zone, "zone", v)
        st[kind] = st.get(kind, 0) + 1
        middle = kind == "한가운데 실투"

        # 치기
        if kind == "빠진 공":
            swing = rng.random() < _p(WILD["swing"], "oswing", v)
            contact = _p(WILD["contact"], "contact", v)
        elif middle:
            swing = rng.random() < _p(zsw, "zswing", v, MIDDLE["swing"])
            contact = _p(zcon, "contact", v, MIDDLE["contact"])
        else:
            swing = rng.random() < (_p(zsw, "zswing", v) if in_zone else _p(osw, "oswing", v))
            contact = _p(zcon if in_zone else ocon, "contact", v)

        label = kind if kind != "빠진 공" else f"빠진 공({wild_dir})"
        if swing:
            if rng.random() < contact:
                if rng.random() < FOUL_SHARE[in_zone]:
                    pitch = "파울"
                    if strikes < 2:
                        strikes += 1
                else:
                    res = _in_play(v, in_zone, middle, rng)
                    if log is not None:
                        log.append((label, "인플레이 " + res))
                    return res
            else:
                pitch = "헛스윙"
                strikes += 1
        elif wild_dir == "몸쪽":
            if log is not None:
                log.append((label, "사구"))
            return "HBP"
        else:
            if wild_dir is not None:
                is_strike = False
            elif middle:
                is_strike = rng.random() < MIDDLE["take_strike"]
            else:
                is_strike = rng.random() < TAKE_STRIKE[in_zone]
            if is_strike:
                pitch = "스트라이크"
                strikes += 1
            else:
                pitch = "볼"
                balls += 1
                if wild_dir == "바닥" and ctx and any(ctx["bases"]) and rng.random() < WP_RATE:
                    _wild_pitch(ctx)
                    pitch = "볼 + 폭투"
        if log is not None:
            log.append((label, pitch + " " + ("삼진" if strikes == 3 else "볼넷" if balls == 4 else f"{balls}-{strikes}")))
        if strikes == 3:
            return "K"
        if balls == 4:
            return "BB"


# ------------------------------------------------------------
# 3-2. 경기 진행 (v1과 같음 + 타석 중 폭투로 주자가 움직임)
# ------------------------------------------------------------
def half_inning(bat_team, pit_team, state, stats, rng=random):
    outs, runs = 0, 0
    ctx = {"bases": [None, None, None], "runs": 0, "stats": stats}
    defense = pit_team.defense()
    while outs < 3:
        pitcher = v1.current_pitcher(pit_team, state)
        batter = bat_team.lineup[state["order"][bat_team.name] % 9]
        state["order"][bat_team.name] += 1
        res = plate_appearance(batter, pitcher, defense, rng, ctx=ctx)
        runs += ctx["runs"]
        ctx["runs"] = 0
        bases = ctx["bases"]
        stats[res] = stats.get(res, 0) + 1
        stats["PA"] = stats.get("PA", 0) + 1
        if res == "K":
            outs += 1
        elif res == "OUT":
            # 희생플라이·병살 단순 처리 (v1과 같음, ⑤에서 다시 만듦)
            if bases[2] and outs < 2 and rng.random() < 0.35:
                runs += 1
                bases[2] = None
            elif bases[0] and outs < 2 and rng.random() < 0.12:
                outs += 1
                bases[0] = None
            outs += 1
        else:
            bases, r = v1.advance(bases, res, batter, rng)
            runs += r
        ctx["bases"] = bases
    return runs


def play_game(home, away, rng=random, stats=None):
    """v1 play_game과 같음 (반 이닝 계산만 v2)"""
    stats = stats if stats is not None else {}
    for t in (home, away):
        for pp in t.rotation + t.bullpen:
            pp.pitches_today = 0
    state = {
        "order": {home.name: 0, away.name: 0},
        "pitcher": {home.name: home.rotation[home.rot_idx % 5], away.name: away.rotation[away.rot_idx % 5]},
    }
    score = {home.name: 0, away.name: 0}
    inning = 0
    while True:
        inning += 1
        score[away.name] += half_inning(away, home, state, stats, rng)
        if inning >= 9 and score[home.name] > score[away.name]:
            break
        score[home.name] += half_inning(home, away, state, stats, rng)
        if inning >= 9 and score[home.name] != score[away.name]:
            break
        if inning >= 12:  # KBO식 12회 무승부
            break
    for t in (home, away):
        t.rot_idx += 1
        for pp in t.bullpen:
            pp.rest_days = 0 if pp.pitches_today > 0 else pp.rest_days + 1
    h, a = score[home.name], score[away.name]
    if h > a:
        home.wins += 1; away.losses += 1
    elif a > h:
        away.wins += 1; home.losses += 1
    else:
        home.ties += 1; away.ties += 1
    stats["R"] = stats.get("R", 0) + h + a
    stats["G"] = stats.get("G", 0) + 1
    return h, a


def play_season(teams, games_vs_each=16, rng=random, stats=None):
    for t in teams:
        t.wins = t.losses = t.ties = 0
    schedule = []
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            for g in range(games_vs_each):
                schedule.append((teams[i], teams[j]) if g % 2 == 0 else (teams[j], teams[i]))
    rng.shuffle(schedule)
    for home, away in schedule:
        play_game(home, away, rng, stats)
    return sorted(teams, key=lambda t: t.wins / max(t.wins + t.losses, 1), reverse=True)


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
    """평균 타자 vs 평균 투수가 TARGET을 내도록 SHIFT를 맞춤 (결과를 SHIFT에 적어 둠)"""
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
        SHIFT["contact"] += 0.8 * (logit(k) - logit(TARGET["k"]))
        SHIFT["zone"] += 0.8 * (logit(bb) - logit(TARGET["bb"]))
        SHIFT["body"] -= logit(hbp) - logit(TARGET["hbp"])
        SHIFT["hr"] -= logit(hr) - logit(TARGET["hr_contact"])
        SHIFT["babip"] -= logit(babip) - logit(TARGET["babip"])
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


def league_average(seasons=3, seed=1):
    """평균 50짜리 10팀으로 시즌을 돌린 리그 평균"""
    rng = random.Random(seed)
    stats = {}
    for _ in range(seasons):
        teams = [make_team(f"T{i}", 50, rng=rng) for i in range(10)]
        play_season(teams, rng=rng, stats=stats)
    s = slash(stats)
    s["R/G(팀)"] = stats["R"] / stats["G"] / 2
    s["사구%"] = stats.get("HBP", 0) / stats["PA"]
    s["폭투/경기"] = stats.get("WP", 0) / stats["G"]
    pitches = sum(stats.get(k, 0) for k in ("보통", "한가운데 실투", "빠진 공"))
    s["한가운데 실투/경기"] = stats.get("한가운데 실투", 0) / stats["G"]
    s["빠진 공/경기"] = stats.get("빠진 공", 0) / stats["G"]
    s["투구/타석"] = pitches / stats["PA"]
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
                standings = play_season(teams, rng=rng)
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
    print("== 리그 평균 (평균 50 팀 10개, 3시즌) — v1과 비교 ==")
    a, b = v1.exp1_league_average(), league_average()
    for k in b:
        print(f"  {k:10s} v1 {a[k]:.3f}   v2 {b[k]:.3f}" if k in a else f"  {k:10s}          v2 {b[k]:.3f}")

    print("\n== 능력치 하나를 50→70 (영향력 배율 1.0, 기획 문서 5.2절과 같은 조건) ==")
    SCALE = 1.0
    for k, s in sensitivity().items():
        print(f"  {k:6s} AVG {s['AVG']:.3f}  OBP {s['OBP']:.3f}  SLG {s['SLG']:.3f}  K% {s['K%']:.3f}  BB% {s['BB%']:.3f}  HR% {s['HR%']:.4f}  타석당 투구 {s['P/PA']:.2f}")
    SCALE = v1.SCALE

    print("\n== 난이도 (영향력 배율 0.35, AI 50±5, 5시즌 평균) ==")
    out, gap = difficulty()
    print("  " + ", ".join(f"+{k}: {v:.3f}" for k, v in out.items()) + f", 1위-꼴찌 차 {gap:.3f}")
