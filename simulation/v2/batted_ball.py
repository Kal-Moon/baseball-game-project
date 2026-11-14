"""5.5절 6 (③-4): 타구 세 값(속도·각도·방향) → MLB 2025 표 → 결과"""
from config import P, ZZ, ZX, SCALE
from batted_table import BATTED


def _ev_bin(v):
    return max(55, min(115, int(v // 5) * 5))


def _la_bin(a):
    return max(-30, min(70, int(a // 10) * 10))


def make_ball(batter, pitcher, q, swing, x, z, t, rng):
    ev = (P["ev0"] + P["ev_q"] * q + P["k_pow_ev"] * (batter.pow - pitcher.stuff) / 10 * SCALE
          + rng.gauss(0, P["ev_sd"]))
    # 변화 = 장타 억제형(땅볼 유도, 2.3절 역할): 변화가 높을수록 맞은 공의 각도가 낮아짐 (4단계 시험)
    la = (P["la0"] + P["la_swing"][swing] + P["la_h"] * (z / ZZ) - P["k_brk_la"] * (pitcher.brk - 50) / 10 * SCALE
          + rng.gauss(0, P["la_sd"]))
    sw = P["dir_swing"] if swing == "당겨치기" else (-P["dir_swing"] if swing == "밀어치기" else 0.0)
    score = P["dir_bias"] + sw + P["dir_x"] * (-x / ZX) + P["dir_t"] * (-t) + rng.gauss(0, P["dir_sd"])
    direction = 0 if score > P["dir_cut"] else (2 if score < -P["dir_cut"] else 1)
    return ev, la, direction


def lookup(ev, la, direction):
    key = (_ev_bin(ev), _la_bin(la), direction)
    if key in BATTED:
        return BATTED[key]
    # 표본이 없는 칸은 가운데 방향 → 가까운 각도
    for k in [(key[0], key[1], 1), (key[0], key[1] - 10, direction), (key[0], key[1] + 10, direction)]:
        if k in BATTED:
            return BATTED[k]
    return (0, 0.0, 0.0, 0.0, 0.0)


def result(batter, pitcher, fielder_dfn, ev, la, direction, rng):
    """표의 확률로 결과. 홈런이 아닌 안타는 그 공을 처리한 야수 수비로 조정 (3.6절)."""
    _, s1, s2, s3, hr = lookup(ev, la, direction)
    k = P["hit_mult"] * (1 - P["k_dfn"] * (fielder_dfn - 50) / 10 * SCALE)
    s1, s2, s3 = s1 * k, s2 * k, s3 * k
    if la < 10:  # 땅볼 단타(내야안타 포함)는 (주루 − 수비) 영향 (3.1절 주루)
        s1 *= 1 + P["k_spd"] * (batter.spd - fielder_dfn) / 10 * SCALE
    r = rng.random()
    for name, p in (("홈런", hr), ("3루타", s3), ("2루타", s2), ("단타", s1)):
        if r < p:
            return name
        r -= p
    return "아웃"
