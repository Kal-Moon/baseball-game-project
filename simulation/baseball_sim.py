"""
야구 게임 밸런스 시뮬레이터 v0
- 목적: 능력치 숫자가 야구다운 결과를 내는지, 어떤 능력치가 얼마나 영향을 주는지 확인
- 능력치 범위: 1~100, 리그 평균 50 (가정)
- 타석 계산: 3단계 (볼넷·삼진 → 홈런 → 인플레이 타구가 안타가 되는지)
- 목표 리그 평균(대략치): 삼진 18%, 볼넷 9%, 사구 1.2%, 홈런 2.2%/타석, BABIP .305
  → 실제 KBO 리그 평균을 확인해서 BASE 값을 맞추는 것이 다음 단계
"""
import math
import random
import statistics
from dataclasses import dataclass, field

# ------------------------------------------------------------
# 1. 기준 확률과 능력치 영향력 (밸런스 조정은 여기서만 하면 됨)
# ------------------------------------------------------------
BASE = {
    "bb": 0.090,       # 볼넷 / 타석
    "hbp": 0.012,      # 사구 / 타석
    "k": 0.180,        # 삼진 / 타석
    "hr_contact": 0.030,  # 홈런 / 컨택(삼진·볼넷·사구 제외 타석)
    "babip": 0.305,    # 인플레이 타구 중 안타 비율
    "double": 0.20,    # 안타 중 2루타 비율
    "triple": 0.02,    # 안타 중 3루타 비율
}

# 능력치 1 표준편차(10) 차이가 로짓(log-odds)을 얼마나 움직이는지
# v1 (투수 역할 분리)
#   구속 = 삼진형, 변화 = 장타 억제형(땅볼 유도), 구위 = 약한 타구, 제구 = 볼넷 억제 + 실투(홈런) 약간 억제
W = {
    "bb":    {"eye": 0.30, "ctl": -0.30},
    "k":     {"con": -0.30, "vel": 0.25, "brk": 0.08, "stuff": 0.05},
    "hr":    {"pow": 0.40, "stuff": -0.10, "vel": -0.05, "brk": -0.22, "ctl": -0.08},
    "babip": {"con": 0.10, "pow": 0.05, "spd": 0.05, "stuff": -0.07, "brk": -0.02, "defense": -0.10},
    "double": {"pow": 0.15, "spd": 0.05, "brk": -0.20},
    "triple": {"spd": 0.40},
}

PITCHES_PER_PA = 3.9

# 능력치 영향력 전체 배율 (1.0 = 위 W 그대로). 난이도 조정은 이 값 하나로 해요.
SCALE = 0.35  # v1 난이도 기준: 리그 평균=5할, +5≈5.6할, +10≈6.5할, +15≈7.2할


def logit(p):
    return math.log(p / (1 - p))


def inv_logit(x):
    return 1 / (1 + math.exp(-x))


def adjust(base_p, weights, values):
    """base_p를 능력치에 따라 로짓 공간에서 조정. values: {이름: 능력치(1~100)}"""
    x = logit(base_p)
    for name, w in weights.items():
        x += SCALE * w * (values[name] - 50) / 10
    return inv_logit(x)


# ------------------------------------------------------------
# 2. 선수와 팀
# ------------------------------------------------------------
@dataclass
class Batter:
    name: str
    con: float  # 정확
    pow: float  # 파워
    eye: float  # 선구
    spd: float  # 주루
    dfn: float  # 수비
    arm: float  # 송구

    def ovr(self):
        return (self.con + self.pow + self.eye + self.spd + self.dfn + self.arm) / 6


@dataclass
class Pitcher:
    name: str
    vel: float    # 구속
    stuff: float  # 구위
    ctl: float    # 제구
    brk: float    # 변화
    sta: float    # 체력 (= 투구 수 한계)
    role: str = "SP"
    pitches_today: int = 0
    rest_days: int = 5

    def ovr(self):
        return (self.vel + self.stuff + self.ctl + self.brk) / 4

    def fatigue_factor(self):
        """투구 수가 체력의 90%를 넘으면 능력치가 떨어짐"""
        ratio = self.pitches_today / max(self.sta, 1)
        if ratio < 0.9:
            return 0.0
        return min((ratio - 0.9) * 50, 15)  # 최대 -15


def clamp(v):
    return max(1.0, min(100.0, v))


@dataclass
class Team:
    name: str
    lineup: list
    rotation: list
    bullpen: list
    wins: int = 0
    losses: int = 0
    ties: int = 0
    rot_idx: int = 0

    def defense(self):
        return statistics.mean((b.dfn + b.arm) / 2 for b in self.lineup)

    def ovr(self):
        bat = statistics.mean(b.ovr() for b in self.lineup)
        pit = statistics.mean(p.ovr() for p in self.rotation + self.bullpen)
        return (bat + pit) / 2


def make_team(name, mean, sd=8, rng=random):
    g = lambda m=mean: clamp(rng.gauss(m, sd))
    lineup = [Batter(f"{name}-B{i+1}", g(), g(), g(), g(), g(), g()) for i in range(9)]
    rotation = [Pitcher(f"{name}-SP{i+1}", g(), g(), g(), g(), clamp(rng.gauss(95, 8)), "SP") for i in range(5)]
    bullpen = [Pitcher(f"{name}-RP{i+1}", g(), g(), g(), g(), clamp(rng.gauss(30, 5)), "RP") for i in range(7)]
    return Team(name, lineup, rotation, bullpen)


# ------------------------------------------------------------
# 3. 타석 계산
# ------------------------------------------------------------
def plate_appearance(b: Batter, p: Pitcher, defense, rng=random):
    f = p.fatigue_factor()
    pv = {"vel": p.vel - f, "stuff": p.stuff - f, "ctl": p.ctl - f, "brk": p.brk - f}
    v = {"con": b.con, "pow": b.pow, "eye": b.eye, "spd": b.spd, "defense": defense, **pv}

    p.pitches_today += PITCHES_PER_PA

    # 1단계: 볼넷·사구·삼진
    p_bb = adjust(BASE["bb"], W["bb"], v)
    p_k = adjust(BASE["k"], W["k"], v)
    r = rng.random()
    if r < p_bb:
        return "BB"
    if r < p_bb + BASE["hbp"]:
        return "HBP"
    if r < p_bb + BASE["hbp"] + p_k:
        return "K"

    # 2단계: 홈런
    if rng.random() < adjust(BASE["hr_contact"], W["hr"], v):
        return "HR"

    # 3단계: 인플레이 타구가 안타가 되는가
    if rng.random() < adjust(BASE["babip"], W["babip"], v):
        r = rng.random()
        p3 = adjust(BASE["triple"], W["triple"], v)
        p2 = adjust(BASE["double"], W["double"], v)
        if r < p3:
            return "3B"
        if r < p3 + p2:
            return "2B"
        return "1B"
    return "OUT"


# ------------------------------------------------------------
# 4. 경기 계산 (주자 진루는 단순화)
# ------------------------------------------------------------
def advance(bases, result, b: Batter, rng=random):
    """bases: [1루, 2루, 3루] 에 주자(Batter 또는 None). 반환: (새 bases, 득점)"""
    runs = 0
    b1, b2, b3 = bases
    if result in ("BB", "HBP"):
        if b1 and b2 and b3:
            runs += 1
        new3 = b3 if not (b1 and b2) else b2
        new2 = b2 if not b1 else b1
        return [b, new2, new3], runs
    if result == "HR":
        return [None, None, None], 1 + sum(x is not None for x in bases)
    if result == "3B":
        return [None, None, b], sum(x is not None for x in bases)
    if result == "2B":
        runs += (b3 is not None) + (b2 is not None)
        new3 = None
        if b1:
            if rng.random() < 0.40 + (b1.spd - 50) / 200:
                runs += 1
            else:
                new3 = b1
        return [None, b, new3], runs
    if result == "1B":
        runs += b3 is not None
        new3, new2 = None, None
        if b2:
            if rng.random() < 0.60 + (b2.spd - 50) / 200:
                runs += 1
            else:
                new3 = b2
        if b1:
            if new3 is None and rng.random() < 0.25 + (b1.spd - 50) / 200:
                new3 = b1
            else:
                new2 = b1
        return [b, new2, new3], runs
    return bases, 0


def half_inning(bat_team: Team, pit_team: Team, state, stats, rng=random):
    outs, runs = 0, 0
    bases = [None, None, None]
    defense = pit_team.defense()
    while outs < 3:
        pitcher = current_pitcher(pit_team, state)
        batter = bat_team.lineup[state["order"][bat_team.name] % 9]
        state["order"][bat_team.name] += 1
        res = plate_appearance(batter, pitcher, defense, rng)
        stats[res] = stats.get(res, 0) + 1
        stats["PA"] = stats.get("PA", 0) + 1
        if res == "K":
            outs += 1
        elif res == "OUT":
            # 희생플라이·병살 단순 처리
            if bases[2] and outs < 2 and rng.random() < 0.35:
                runs += 1
                bases[2] = None
            elif bases[0] and outs < 2 and rng.random() < 0.12:
                outs += 1
                bases[0] = None
            outs += 1
        else:
            bases, r = advance(bases, res, batter, rng)
            runs += r
    return runs


def current_pitcher(team: Team, state):
    key = team.name
    p = state["pitcher"][key]
    if p.pitches_today >= p.sta:  # 체력 한계면 교체
        fresh = [r for r in team.bullpen if r.rest_days >= 1 and r.pitches_today == 0 and r is not p]
        if fresh:
            p = max(fresh, key=lambda x: x.ovr())
            state["pitcher"][key] = p
    return p


def play_game(home: Team, away: Team, rng=random, stats=None):
    stats = stats if stats is not None else {}
    for t in (home, away):
        for pp in t.rotation + t.bullpen:
            pp.pitches_today = 0
    state = {
        "order": {home.name: 0, away.name: 0},
        "pitcher": {home.name: home.rotation[home.rot_idx % 5], away.name: away.rotation[away.rot_idx % 5]},
    }
    used = set()
    score = {home.name: 0, away.name: 0}
    inning = 0
    while True:
        inning += 1
        score[away.name] += half_inning(away, home, state, stats, rng)
        used.add(id(state["pitcher"][home.name]))
        if inning >= 9 and score[home.name] > score[away.name]:
            break
        score[home.name] += half_inning(home, away, state, stats, rng)
        used.add(id(state["pitcher"][away.name]))
        if inning >= 9 and score[home.name] != score[away.name]:
            break
        if inning >= 12:  # KBO식 12회 무승부
            break
    # 휴식일 처리
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
# 5. 실험
# ------------------------------------------------------------
def slash(stats):
    pa = stats["PA"]
    hits = sum(stats.get(k, 0) for k in ("1B", "2B", "3B", "HR"))
    ab = pa - stats.get("BB", 0) - stats.get("HBP", 0)
    tb = stats.get("1B", 0) + 2 * stats.get("2B", 0) + 3 * stats.get("3B", 0) + 4 * stats.get("HR", 0)
    return {
        "AVG": hits / ab,
        "OBP": (hits + stats.get("BB", 0) + stats.get("HBP", 0)) / pa,
        "SLG": tb / ab,
        "K%": stats.get("K", 0) / pa,
        "BB%": stats.get("BB", 0) / pa,
        "HR%": stats.get("HR", 0) / pa,
    }


def exp1_league_average(seasons=3, seed=1):
    """평균 50짜리 10팀으로 시즌을 돌려 리그 평균 기록이 야구다운지 확인"""
    rng = random.Random(seed)
    stats = {}
    for _ in range(seasons):
        teams = [make_team(f"T{i}", 50, rng=rng) for i in range(10)]
        play_season(teams, rng=rng, stats=stats)
    s = slash(stats)
    s["R/G(팀)"] = stats["R"] / stats["G"] / 2
    return s


def exp2_batter_sensitivity(n_pa=200_000, seed=2):
    """평균 타자의 능력치 하나를 +20(평균 50 → 70) 했을 때 기록 변화"""
    rng = random.Random(seed)
    base_p = Pitcher("P", 50, 50, 50, 50, 10**9)
    rows = {}
    for stat in ["기준", "con", "pow", "eye", "spd"]:
        b = Batter("B", 50, 50, 50, 50, 50, 50)
        if stat != "기준":
            setattr(b, stat, 70)
        st = {}
        for _ in range(n_pa):
            base_p.pitches_today = 0
            r = plate_appearance(b, base_p, 50, rng)
            st[r] = st.get(r, 0) + 1
        st["PA"] = n_pa
        rows[stat] = slash(st)
    return rows


def exp3_pitcher_sensitivity(n_pa=200_000, seed=3):
    """평균 투수의 능력치 하나를 +20 했을 때 피안타율·피OPS 변화"""
    rng = random.Random(seed)
    b = Batter("B", 50, 50, 50, 50, 50, 50)
    rows = {}
    for stat in ["기준", "vel", "stuff", "ctl", "brk"]:
        p = Pitcher("P", 50, 50, 50, 50, 10**9)
        if stat != "기준":
            setattr(p, stat, 70)
        st = {}
        for _ in range(n_pa):
            p.pitches_today = 0
            r = plate_appearance(b, p, 50, rng)
            st[r] = st.get(r, 0) + 1
        st["PA"] = n_pa
        rows[stat] = slash(st)
    return rows


def exp4_ovr_spread(spread, trials=30, seed=4):
    """내 팀 OVR=50, AI 9팀은 50±spread 범위에 고르게 배치. 내 팀 성적 분포"""
    rng = random.Random(seed)
    ranks, win_pcts, top_gap = [], [], []
    for _ in range(trials):
        offsets = [(-spread + 2 * spread * i / 8) for i in range(9)]
        teams = [make_team("ME", 50, rng=rng)] + [make_team(f"AI{i}", 50 + o, rng=rng) for i, o in enumerate(offsets)]
        standings = play_season(teams, rng=rng)
        me = next(t for t in teams if t.name == "ME")
        ranks.append(standings.index(me) + 1)
        win_pcts.append(me.wins / (me.wins + me.losses))
        wp = [t.wins / (t.wins + t.losses) for t in standings]
        top_gap.append(wp[0] - wp[-1])
    return {
        "평균 순위": statistics.mean(ranks),
        "1위 비율": sum(r == 1 for r in ranks) / trials,
        "5위 이내(가을야구) 비율": sum(r <= 5 for r in ranks) / trials,
        "내 팀 승률 평균": statistics.mean(win_pcts),
        "1위-꼴찌 승률 차": statistics.mean(top_gap),
    }


def exp5_difficulty(scale, my_offsets=(0, 5, 10, 15), spread=5, trials=10, seed=5):
    """영향력 배율(scale)별로, AI 9팀은 50±spread, 내 팀은 50+offset일 때 내 팀 승률.
    리그 전체 1위-꼴찌 승률 차(보조 지표)도 함께 반환."""
    global SCALE
    old = SCALE
    SCALE = scale
    rng = random.Random(seed)
    out = {}
    gaps = []
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
        out[off] = statistics.mean(wps)
    SCALE = old
    return out, statistics.mean(gaps)


if __name__ == "__main__":
    print("== 실험 1: 리그 평균 기록 (평균 50 팀 10개, 3시즌) ==")
    for k, v in exp1_league_average().items():
        print(f"  {k}: {v:.3f}")

    print("\n== 실험 2: 타자 능력치 하나를 50→70 ==")
    for k, v in exp2_batter_sensitivity().items():
        print(f"  {k:5s} AVG {v['AVG']:.3f}  OBP {v['OBP']:.3f}  SLG {v['SLG']:.3f}  K% {v['K%']:.3f}  BB% {v['BB%']:.3f}  HR% {v['HR%']:.4f}")

    print("\n== 실험 3: 투수 능력치 하나를 50→70 (상대 평균 타자) ==")
    for k, v in exp3_pitcher_sensitivity().items():
        print(f"  {k:5s} 피안타율 {v['AVG']:.3f}  피출루 {v['OBP']:.3f}  피장타 {v['SLG']:.3f}  K% {v['K%']:.3f}  BB% {v['BB%']:.3f}  HR% {v['HR%']:.4f}")

    print("\n== 실험 4: AI 팀 오버롤 분포 폭에 따른 내 팀(50) 성적, 30시즌 ==")
    for spread in (5, 10):
        r = exp4_ovr_spread(spread)
        print(f"  ±{spread}: " + ", ".join(f"{k} {v:.3f}" for k, v in r.items()))
