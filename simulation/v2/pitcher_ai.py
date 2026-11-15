"""5.5절 1~2: 투수가 구종·노리는 곳을 고르고, 원 안에서 공이 간 곳이 정해짐"""
import math

from config import P, ZX, ZZ, SCALE, GRADE_MULT
from tables import COUNT, ZONE_BY_TYPE, ZONE_AVG


def _weighted(items, rng):
    tot = sum(w for _, w in items)
    r = rng.random() * tot
    for it, w in items:
        r -= w
        if r <= 0:
            return it
    return items[-1][0]


def choose_pitch(pitcher, count, rng):
    """카운트별 패스트볼 계열 비율을 먼저, 나머지는 구사율대로 (③-2)."""
    fb_share = COUNT[count][1]
    fbs = [(p, p.use) for p in pitcher.pitches if p.family == "패스트볼"]
    others = [(p, p.use) for p in pitcher.pitches if p.family != "패스트볼"]
    if not others or (fbs and rng.random() < fb_share):
        return _weighted(fbs or others, rng)
    return _weighted(others, rng)


def _side(pitch, rng, chase):
    """존 끝·유인구를 어느 쪽에 둘지. 패스트볼은 위·옆, 브레이킹은 아래·바깥, 오프스피드는 아래."""
    if pitch.family == "패스트볼":
        inside = 0.45 if pitch.name == "싱커" else 0.25   # 싱커는 몸쪽 승부가 많음 (사구 조사 3장)
        w = [("high", 0.40), ("in", inside), ("out", 0.60 - inside), ("low", 0.15)]
    elif pitch.family == "브레이킹":
        w = [("low", 0.55), ("out", 0.35), ("in", 0.05), ("high", 0.05)]
    else:
        w = [("low", 0.75), ("out", 0.15), ("in", 0.05), ("high", 0.05)]
    return _weighted(w, rng)


def _point_on_side(side, depth, rng):
    """side 쪽 존 테두리에서 depth만큼 바깥(음수면 안쪽)."""
    if side in ("high", "low"):
        z = (ZZ + depth) * (1 if side == "high" else -1)
        x = rng.uniform(-ZX, ZX)
    else:
        x = (ZX + depth) * (-1 if side == "in" else 1)
        z = rng.uniform(-ZZ, ZZ)
    return x, z


def choose_target(pitch, count, rng):
    """노리는 곳 세 종류: 존 안 / 존 끝 / 유인구 (③-2). 노린 곳 ≠ 공이 간 곳이라 존 안을 결과보다 많이 노림."""
    want = COUNT[count][0] * (ZONE_BY_TYPE[pitch.name] / ZONE_AVG) - P["aim_shift"]
    p_edge = 0.30
    p_in = min(0.70, max(0.0, (want - 0.255) / 0.70))   # 존 안 ≈ 0.85·p_in + 0.5·0.3 + 0.15·p_chase 로 푼 값
    r = rng.random()
    if r < p_in:
        return rng.uniform(-ZX + 4, ZX - 4), rng.uniform(-ZZ + 4, ZZ - 4), "in"
    if r < p_in + p_edge:
        x, z = _point_on_side(_side(pitch, rng, False), -P["edge_in"], rng)
        return x, z, "edge"
    x, z = _point_on_side(_side(pitch, rng, True), rng.uniform(P["chase_min"], P["chase_max"]), rng)
    return x, z, "chase"


def fatigue_mult(pitcher):
    """⑤-5: 노랑(70%)부터 원이 커져 한계(100%)에서 1.15배, 한계를 넘으면 최대 1.3배 ★."""
    ratio = pitcher.pitches_today / max(pitcher.sta, 1)
    if ratio < 0.7:
        return 1.0
    if ratio < 1.0:
        return 1.0 + (ratio - 0.7) * 0.5
    return min(1.3, 1.15 + (ratio - 1.0) * 0.75)


def locate(pitcher, pitch, target, rng):
    """원 안에서 공이 간 곳. 원 = 제구 × 구종 등급 × 체력. 낮은 확률로 실투 (한가운데 / 빠진 공)."""
    d = (pitcher.ctl - 50) / 10 * SCALE
    p_mis = P["mistake"] * math.exp(-P["k_ctl_mistake"] * d) * fatigue_mult(pitcher)
    if rng.random() < p_mis:
        if rng.random() < P["mistake_meatball"]:
            return rng.gauss(0, 2.5), rng.gauss(0, 2.5), "meatball"
        side = _weighted([("low", 0.6), ("in", 0.2), ("out", 0.1), ("high", 0.1)], rng)
        x, z = _point_on_side(side, rng.uniform(10, 20), rng)
        return x, z, "wild"
    sd = P["miss_sd"] * math.exp(-P["k_ctl_miss"] * d) * GRADE_MULT[pitch.grade] * fatigue_mult(pitcher)
    return target[0] + rng.gauss(0, sd), target[1] + rng.gauss(0, sd), "normal"
