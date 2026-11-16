"""
직접 플레이 한 타석 모델 v1 (2026-11-16, 시뮬레이션 단계 ②)

목적: 유저가 직접 칠 때(공 하나하나: 투구 위치 → 스윙 판단 → 타이밍 7단계 → 코스·스윙 궁합 → 결과)
      평균 능력치 + 보통 유저의 결과가 자동 경기(baseball_sim.py v2, KBO 2026)와 같아지도록 맞춘다.
      (KAL 결정 2026-11-16: "평균 유저 = 자동 경기")

좌표: 스트라이크 존을 가로·세로 -1 ~ 1 로 둔 단위. x < 0 이 타자 몸쪽.
능력치 효과(선구·정확·파워·구위·변화)의 계수는 단계 ③에서 정한다. 여기서는 모두 평균(50)이라 0.
"""
import random
from dataclasses import dataclass

# ------------------------------------------------------------
# 1. 유저 실력 (스윙 판단은 MLB 2026 현실 타자 평균, 타이밍 분포는 가정 → 타격 시험판 기록으로 고침)
# ------------------------------------------------------------
@dataclass
class UserSkill:
    name: str
    zone_swing: float   # 존 안 공에 스윙하는 비율
    chase: float        # 존 밖 공에 스윙하는 비율 (볼에 속는 비율)
    timing: dict        # 스윙했을 때 타이밍 분포: 너무 / 빠름·늦음 / 좋음 / 완벽
    compat: tuple       # 코스·스윙 궁합 (좋음, 보통, 나쁨) 비율


USERS = {
    "서툰": UserSkill("서툰", 0.60, 0.40, {"too": 0.40, "near": 0.35, "good": 0.20, "perfect": 0.05}, (0.25, 0.45, 0.30)),
    "보통": UserSkill("보통", 0.667, 0.305, {"too": 0.25, "near": 0.35, "good": 0.30, "perfect": 0.10}, (0.40, 0.40, 0.20)),
    "잘함": UserSkill("잘함", 0.72, 0.22, {"too": 0.15, "near": 0.30, "good": 0.35, "perfect": 0.20}, (0.55, 0.35, 0.10)),
}

# ------------------------------------------------------------
# 2. 조정값 (보통 유저 + 평균 능력치가 목표에 맞도록 조정한 값, 현실에서 직접 잰 값이 아님)
# ------------------------------------------------------------
P = {
    # 투구 위치 (상대 AI 투수, 제구 50)
    "aim_zone": 0.47,        # 존 안을 노리는 비율 (볼카운트로 조금씩 바뀜)
    "sigma": 0.42,           # 원 크기에 해당하는 흩어짐 (제구 50)
    "miss": 0.03,            # 실투 비율 (공 하나당)
    "miss_center": 0.85,     # 실투 중 한가운데 실투 비중 (나머지는 빠진 공)
    "body_x": -2.13,         # 이보다 몸쪽이면 사구 (타자 몸 영역)
    # 스윙 결과: 타이밍별 [헛스윙, 파울, 약한, 보통, 강한 타구] (존 안 공)
    "out_zone_penalty": 0.6, # 존 밖 공은 이 확률로 타이밍이 한 단계 나빠짐
    "out_zone_whiff": 0.24,  # 존 밖 공은 맞힐 타구가 이 확률로 헛스윙이 됨
    # 타구 질 → 결과 [안타 확률, 그중 2루타, 3루타, 홈런 확률(타구 전체 기준)]
    "weak":   (0.12, 0.05, 0.00, 0.000),
    "normal": (0.362, 0.20, 0.02, 0.011),
    "strong": (0.62, 0.32, 0.03, 0.140),
}

GRADES = ["too", "near", "good", "perfect"]
OUTCOME = {  # [whiff, foul, weak, normal, strong]
    "too":     [0.45, 0.42, 0.13, 0.00, 0.00],
    "near":    [0.06, 0.52, 0.24, 0.18, 0.00],
    "good":    [0.00, 0.40, 0.14, 0.32, 0.14],
    "perfect": [0.00, 0.22, 0.05, 0.25, 0.48],
}


# 선구 (KAL 2026-11-16 확정: 공이 느려지는 효과는 그대로, 느려진 시간을 "볼을 고르는 데" 주로 씀)
#   느려짐 = 계수 × (선구 − 상대 구속), 상한 +10%(느려짐) / −5%(빨라짐).
#   효과 1(주): 느려진 만큼 볼에 속는 비율이 줄어듦.  효과 2(부): 타이밍이 한 단계 좋아질 확률이 조금 늘어남.
#   현실에서 잰 값이 아니고 자동 경기(선구 50→70: 볼넷 +1.9%p, 출루율 +.012)에 맞춘 조정값.
#   A안 확정 (KAL 2026-11-16): 출루율 +.012에 맞춤 (볼넷 +1.2%p, 삼진 −0.7%p로 나타남).
EYE = {"coef": 0.0025, "cap_slow": 0.10, "cap_fast": -0.05, "chase": 2.0, "timing": 0.5}


def slowdown(eye_diff):
    """eye_diff = (선구 − 50) − 구속 무게 × (구속 − 50)  (2026-11-16 구속 확정 뒤)"""
    return max(EYE["cap_fast"], min(EYE["cap_slow"], EYE["coef"] * eye_diff))


# 구속 (KAL 2026-11-16 확정: 선구 대결에서는 구속 무게를 작게, 주된 효과는 공 자체가 빨라 타이밍이 늦어짐)
#   ① 선구 대결: 느려짐 = 0.25% × ((선구 − 50) − eye_w × (구속 − 50))
#   ② 구속만: 스윙할 때 타이밍이 한 단계 나빠질 확률 = late × (구속 − 50). 상한 구속 +20 ~ −40점.
VEL = {"eye_w": 0.1, "late": 0.0035, "whiff": 2.0, "cap_pos": 20, "cap_neg": -40, "neg_scale": 1.0}  # 임시값(출루율 맞춤안), KAL 결정 대기


def late_level(vel):
    e = VEL["late"] * max(VEL["cap_neg"], min(VEL["cap_pos"], vel - 50))
    return e if e >= 0 else e * VEL["neg_scale"]


# 정확 ↔ 변화 (KAL 2026-11-16 확정: 두 효과로 나눔, 자동 경기 +20 효과에 맞춘 조정값)
#   ① 헛스윙 쪽 = 정확 대 변화. 맞대결 값 = (정확 − 50) − 0.25 × (변화 − 50)  (변화 무게는 정확의 0.25배)
#      효과 = 계수 × 맞대결 값, 상한: 유리한 쪽 +40점, 불리한 쪽 −20점에 해당하는 크기 (선구와 같은 방식).
#      빗나간 스윙(너무·빠름·늦음, 존 밖 공)의 헛스윙이 파울·빗맞은 타구로 바뀌고, 빠름·늦음의 약한 타구가 쓸 만한 타구로 바뀜.
#      코스·스윙 궁합이 나쁠 때 타구가 나빠지는 확률도 줄어듦. 완벽·좋음은 건드리지 않음.
#   ② 장타 쪽 = 변화만. 맞힌 타구가 한 단계 약해질 확률 (궁합 판단이 어려워 빗맞음). 상한: 변화 −40 ~ +20점.
CON = {"coef": 0.016, "brk_weight": 0.25, "cap_pos": 40, "cap_neg": -20, "stuff_weight": 0.16, "to_foul": 0.7, "upgrade": 2.0, "neg_whiff": 0.55, "neg_down": 2.0}
BRK = {"coef": 0.008, "cap_pos": 20, "cap_neg": -40, "neg_scale": 0.4}


def contact_level(con, brk, st=50):
    lv = (con - 50) - CON["brk_weight"] * (brk - 50) - CON["stuff_weight"] * (st - 50)
    e = CON["coef"] * max(CON["cap_neg"], min(CON["cap_pos"], lv))
    return e


def break_level(brk):
    e = BRK["coef"] * max(BRK["cap_neg"], min(BRK["cap_pos"], brk - 50))
    return e if e >= 0 else e * BRK["neg_scale"]   # 보통 타구가 강한 타구보다 많아서 줄임


# 파워 ↔ 구위 (KAL 2026-11-16 확정: 정확 ↔ 변화처럼 두 효과로 나눔, 자동 경기 +20 효과에 맞춘 조정값)
#   ① 장타 쪽 = 파워 대 구위. 맞대결 값 = (파워 − 50) − w × (구위 − 50), 상한 +40 / −20점.
#      강한 타구의 홈런 확률 × (1 + hr × 값), 보통 타구가 강한 타구로 바뀔 확률 = up × 값 × 타이밍 가중치(완벽일수록 큼).
#   ② 먹힌 타구 쪽 = 구위만. 보통 타구가 약한 타구로 (배트에 밀림). 상한 구위 +20 ~ −40점.
POW = {"stuff_weight": 0.3, "hr": 0.008, "up": 0.01, "neg_up": 1.7, "cap_pos": 40, "cap_neg": -20}
TIMING_W = [0.0, 0.3, 0.7, 1.0]   # 너무 · 빠름/늦음 · 좋음 · 완벽
STF = {"coef": 0.004, "cap_pos": 20, "cap_neg": -40, "neg_scale": 0.3}


def power_level(pw, st):
    return max(POW["cap_neg"], min(POW["cap_pos"], (pw - 50) - POW["stuff_weight"] * (st - 50)))


def stuff_level(st):
    e = STF["coef"] * max(STF["cap_neg"], min(STF["cap_pos"], st - 50))
    return e if e >= 0 else e * STF["neg_scale"]


# 실력 차이 줄이기 (KAL 2026-11-16, B안: 잘함이 보통보다 타율 약 +.040)
#   타이밍 단계별 결과표를 "보통 유저 평균 결과" 쪽으로 SKILL_BLEND 만큼 당김. 1.0 = 원래 표, 0 = 단계 차이 없음.
#   완벽이 항상 가장 좋다는 순서는 유지됨 (섞어도 순서가 바뀌지 않음).
SKILL_BLEND = 0.35
COMPAT_EFFECT = 0.4   # 코스·스윙 궁합 효과 크기 (1.0 = 원래)
_BASE_OUTCOME = {k: list(v) for k, v in OUTCOME.items()}


def set_blend(blend, compat=None):
    global SKILL_BLEND, COMPAT_EFFECT
    SKILL_BLEND = blend
    if compat is not None:
        COMPAT_EFFECT = compat
    w = USERS["보통"].timing
    avg = [sum(w[g] * _BASE_OUTCOME[g][i] for g in GRADES) for i in range(5)]
    for g in GRADES:
        OUTCOME[g] = [blend * a + (1 - blend) * m for a, m in zip(_BASE_OUTCOME[g], avg)]


def pick(rng, items, weights):
    r = rng.random() * sum(weights)
    for it, w in zip(items, weights):
        r -= w
        if r < 0:
            return it
    return items[-1]


def pitch_location(rng, balls, strikes):
    """상대 AI 투수가 던진 공의 위치와 종류 ('normal' / 'center' 한가운데 실투 / 'wild' 빠진 공)"""
    if rng.random() < P["miss"]:
        if rng.random() < P["miss_center"]:
            return rng.gauss(0, 0.2), rng.gauss(0, 0.2), "center"
        side = rng.choice([-1, 1])
        return side * rng.uniform(1.8, 2.6), rng.uniform(-1.5, 1.5), "wild"
    aim = P["aim_zone"] + (0.2 if balls == 3 else 0) - (0.12 if strikes == 2 and balls < 2 else 0)
    if rng.random() < aim:
        ax, ay = rng.uniform(-0.85, 0.85), rng.uniform(-0.85, 0.85)
    else:
        if rng.random() < 0.5:
            ax, ay = rng.choice([-1, 1]) * rng.uniform(1.15, 1.5), rng.uniform(-1, 1)
        else:
            ax, ay = rng.uniform(-1, 1), rng.choice([-1, 1]) * rng.uniform(1.15, 1.5)
    return ax + rng.gauss(0, P["sigma"]), ay + rng.gauss(0, P["sigma"]), "normal"


def in_zone(x, y):
    return abs(x) <= 1 and abs(y) <= 1


def swing_result(rng, user: UserSkill, zone, kind, slow=0.0, ce=0.0, be=0.0, pl=0.0, se=0.0, le=0.0):
    g = GRADES.index(pick(rng, GRADES, [user.timing[k] for k in GRADES]))
    if slow > 0 and rng.random() < EYE["timing"] * slow:
        g = min(3, g + 1)      # 공이 느려져 타이밍이 한 단계 좋아짐 (작게)
    elif slow < 0 and rng.random() < -EYE["timing"] * slow:
        g = max(0, g - 1)      # 공이 빨라져 타이밍이 한 단계 나빠짐
    if le > 0 and rng.random() < le:
        g = max(0, g - 1)      # 구속: 공 자체가 빨라 늦음
    elif le < 0 and rng.random() < -le:
        g = min(3, g + 1)
    if not zone and rng.random() < P["out_zone_penalty"]:
        g = max(0, g - 1)
    if kind == "center":
        g = min(3, g + 1)  # 한가운데 실투는 치기 쉬움 (무브먼트 감소)
    res = pick(rng, ["whiff", "foul", "weak", "normal", "strong"], OUTCOME[GRADES[g]])
    if not zone and res != "whiff" and rng.random() < P["out_zone_whiff"]:
        res = "whiff"  # 존 밖 공은 배트에 맞히기 어려움
    if le != 0 and res == "foul" and rng.random() < abs(le) * VEL["whiff"]:
        res = "whiff" if le > 0 else res   # 구속: 공이 빨라 파울이 될 공을 놓침
    elif le < 0 and res == "whiff" and rng.random() < -le * VEL["whiff"]:
        res = "foul"
    missed = g <= 1 or not zone   # 빗나간 스윙 (정확이 작동하는 곳)
    if missed and ce > 0:
        if res == "whiff" and rng.random() < ce:
            res = "foul" if rng.random() < CON["to_foul"] else "weak"   # 커트하거나 빗맞힘
        elif g == 1 and res == "weak" and rng.random() < ce * CON["upgrade"]:
            res = "normal"   # 빠름·늦음에서도 쓸 만한 타구
    elif missed and ce < 0:
        # 정확이 낮을 때: 자동 경기(정확 30 = 타율 −.024, 삼진 +3.5%p)에 맞춰 헛스윙은 적게, 약한 타구는 많게
        if res in ("foul", "weak") and rng.random() < -ce * CON["neg_whiff"]:
            res = "whiff"
        elif g == 1 and res == "normal" and rng.random() < -ce * CON["neg_down"]:
            res = "weak"
    if res in ("weak", "normal", "strong"):
        c = pick(rng, ["good", "mid", "bad"], user.compat)
        order = ["weak", "normal", "strong"]
        bad_p = 0.5 * COMPAT_EFFECT * (1 - max(-1, min(1, ce)))
        i = order.index(res) + (1 if c == "good" and rng.random() < 0.3 * COMPAT_EFFECT else 0) - (1 if c == "bad" and rng.random() < bad_p else 0)
        if be > 0 and i == 2 and rng.random() < be:
            i = 1     # 변화: 궁합 판단이 어려워 빗맞음 → 강한 타구가 보통으로 (장타 억제)
        elif be < 0 and i == 1 and rng.random() < -be:
            i = 2
        i = max(0, min(2, i))
        up = POW["up"] * pl * TIMING_W[g]
        if up > 0 and i == 1 and rng.random() < up:
            i = 2     # 파워: 잘 맞힌 타구가 더 강해짐
        elif up < 0 and i == 2 and rng.random() < -up * POW["neg_up"]:
            i = 1
        if se > 0 and i == 1 and rng.random() < se:
            i = 0     # 구위: 배트에 밀려 먹힌 타구
        elif se < 0 and i == 0 and rng.random() < -se:
            i = 1
        res = order[i]
    return res


def ball_in_play(rng, q, hr_mult=1.0):
    hit, d2, d3, hr = P[q]
    hr = hr * hr_mult
    if rng.random() < hr:
        return "HR"
    if rng.random() < hit:
        r = rng.random()
        return "3B" if r < d3 else "2B" if r < d3 + d2 else "1B"
    return "OUT"


def plate_appearance(rng, user: UserSkill, log, eye_diff=0, con=50, brk=50, pw=50, st=50, vel=50):
    slow = slowdown(eye_diff - VEL["eye_w"] * (vel - 50))
    le = late_level(vel)
    ce, be = contact_level(con, brk, st), break_level(brk)
    pl, se = power_level(pw, st), stuff_level(st)
    hr_mult = max(0.0, 1 + POW["hr"] * pl)
    balls = strikes = 0
    while True:
        x, y, kind = pitch_location(rng, balls, strikes)
        zone = in_zone(x, y)
        log["pitches"] += 1
        log["zone"] += zone
        p_sw = user.zone_swing if zone else user.chase * (1 - EYE["chase"] * slow) * (0.7 if abs(x) > 1.6 or abs(y) > 1.6 else 1.0)
        if strikes == 2:
            p_sw = min(0.95, p_sw + (0.15 if zone else 0.05))  # 2스트라이크: 존 안 공은 더 지킴
        if rng.random() < p_sw:
            log["swings"] += 1
            log["zswings" if zone else "oswings"] += 1
            res = swing_result(rng, user, zone, kind, slow, ce, be, pl, se, le)
            if res == "whiff":
                log["whiffs"] += 1
                log["zwhiffs" if zone else "owhiffs"] += 1
                strikes += 1
            elif res == "foul":
                log["fouls"] += 1
                strikes = min(2, strikes + 1)
            else:
                return ball_in_play(rng, res, hr_mult)
            if strikes == 3:
                return "K"
            continue
        if x < P["body_x"]:
            return "HBP"
        if zone:
            strikes += 1
            if strikes == 3:
                return "K"
        else:
            balls += 1
            if balls == 4:
                return "BB"


def run(user_name="보통", n=200_000, seed=1, eye_diff=0, con=50, brk=50, pw=50, st=50, vel=50):
    import os; n = int(os.environ.get("N", n))
    rng = random.Random(seed)
    user = USERS[user_name]
    log = {k: 0 for k in ("pitches", "zone", "swings", "zswings", "oswings", "whiffs", "zwhiffs", "owhiffs", "fouls")}
    c = {}
    for _ in range(n):
        r = plate_appearance(rng, user, log, eye_diff, con, brk, pw, st, vel)
        c[r] = c.get(r, 0) + 1
    pa = n
    hits = sum(c.get(k, 0) for k in ("1B", "2B", "3B", "HR"))
    ab = pa - c.get("BB", 0) - c.get("HBP", 0)
    tb = c.get("1B", 0) + 2 * c.get("2B", 0) + 3 * c.get("3B", 0) + 4 * c.get("HR", 0)
    bip = ab - c.get("K", 0) - c.get("HR", 0)
    zone_n = log["zone"]; out_n = log["pitches"] - zone_n
    return {
        "AVG": hits / ab, "OBP": (hits + c.get("BB", 0) + c.get("HBP", 0)) / pa, "SLG": tb / ab,
        "BABIP": (hits - c.get("HR", 0)) / bip,
        "K%": c.get("K", 0) / pa, "BB%": c.get("BB", 0) / pa, "HBP%": c.get("HBP", 0) / pa, "HR%": c.get("HR", 0) / pa,
        "P/PA": log["pitches"] / pa, "Zone%": zone_n / log["pitches"],
        "Swing%": log["swings"] / log["pitches"], "ZSwing%": log["zswings"] / zone_n, "Chase%": log["oswings"] / out_n,
        "Whiff/Sw": log["whiffs"] / log["swings"],
        "ZWhiff": log["zwhiffs"] / max(1, log["zswings"]), "OWhiff": log["owhiffs"] / max(1, log["oswings"]),
        "Foul/Sw": log["fouls"] / log["swings"],
    }


# 목표: 타석 결과 = KBO 2026 (자동 경기 v2와 같음), 공 하나 단위 = MLB 2026 (KBO는 공 단위 공개 자료 없음)
TARGET = {
    "AVG": .268, "OBP": .346, "SLG": .404, "BABIP": .317, "K%": .195, "BB%": .094, "HBP%": .0148, "HR%": .0241,
    "P/PA": 3.89, "Zone%": .475, "Swing%": .477, "ZSwing%": .667, "Chase%": .305, "Whiff/Sw": .251,
    "ZWhiff": .161, "OWhiff": .429, "Foul/Sw": .379,
}

if __name__ == "__main__":
    set_blend(SKILL_BLEND, COMPAT_EFFECT)
    rows = {u: run(u) for u in USERS}
    print(f"{'':10s}" + "".join(f"{u:>9s}" for u in rows) + f"{'목표':>9s}")
    for k in TARGET:
        print(f"{k:10s}" + "".join(f"{rows[u][k]:9.3f}" for u in rows) + f"{TARGET[k]:9.3f}")
