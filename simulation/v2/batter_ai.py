"""5.5절 3~4 (③-3): AI 타자가 사람과 같은 입력(칠지 말지·타이밍·스윙 종류)을 만듦"""
import math

from config import P, ZX, ZZ, SCALE
from tables import COUNT, COUNT_SWING_ADJ, CHASE_ADJ

SWINGS = ["레벨", "어퍼", "다운", "당겨치기", "밀어치기"]


def inv_logit(x):
    return 1 / (1 + math.exp(-x))


def out_dist(x, z):
    """존 밖으로 얼마나 벗어났나 (인치, 존 안이면 0)."""
    dx = max(0.0, abs(x) - ZX)
    dz = max(0.0, abs(z) - ZZ)
    return math.hypot(dx, dz)


def decide_swing(batter, pitcher, pitch, x, z, count, rng):
    adj = COUNT_SWING_ADJ[count]
    d = out_dist(x, z)
    if d == 0:
        p = inv_logit(P["swing_in"] + adj)
    else:
        eye_gap = (batter.eye - pitcher.vel) / 10 * SCALE
        p = inv_logit(P["swing_out"] + adj + CHASE_ADJ[pitch.name]
                      - P["k_eye_chase"] * eye_gap - P["chase_dist"] * d)
    return rng.random() < p


def timing(batter, pitcher, pitch, count, rng):
    """노림(패스트볼 / 변화구)과 실제 속도 차이로 밀리고, 구속이 높을수록 흩어짐. t < 0 = 빠름."""
    guess_fb = rng.random() < COUNT[count][1]
    expect = 1.0 if guess_fb else P["off_expect"]
    # 예상보다 느린 공(ratio 작음)이 오면 빨리 휘두름 → 음수
    shift = -(expect - pitch.ratio) / 0.10 * P["t_shift"] * P["t_adjust"]
    sd = P["t_sd"] * math.exp(P["k_vel_t"] * (pitcher.vel - 50) / 10 * SCALE
                              - P["k_eye_t"] * (batter.eye - pitcher.vel) / 10 * SCALE)
    return rng.gauss(shift, sd)


def timing_grade(t):
    a = abs(t)
    if a < 0.5:
        return "완벽"
    if a < 1.5:
        return "좋음"
    if a < 2.5:
        return "빠름" if t < 0 else "늦음"
    return "너무 빠름" if t < 0 else "너무 늦음"


def region(x, z):
    """코스 궁합 구역 (3.1절): 가운데 원 / 위 / 아래 / 몸쪽 / 바깥쪽 (존 밖 공은 가까운 쪽)."""
    if math.hypot(x, z) < P["center_r"]:
        return "가운데"
    if abs(z) / ZZ >= abs(x) / ZX:
        return "위" if z > 0 else "아래"
    return "몸쪽" if x < 0 else "바깥쪽"


MATCH = {"가운데": "레벨", "위": "다운", "아래": "어퍼", "몸쪽": "당겨치기", "바깥쪽": "밀어치기"}
OPPOSITE = {"위": "어퍼", "아래": "다운", "몸쪽": "밀어치기", "바깥쪽": "당겨치기"}


def choose_swing_type(pitcher, x, z, count, rng):
    reg = region(x, z)
    p_match = inv_logit(P["match_base"] - P["k_brk_match"] * (pitcher.brk - 50) / 10 * SCALE)
    if rng.random() < p_match:
        return MATCH[reg]
    p_level = P["level_fallback"] + (P["two_strike_level"] if count[1] == 2 else 0)
    if rng.random() < min(1.0, p_level):
        return "레벨"
    return rng.choice([s for s in SWINGS if s != MATCH[reg]])


def compat(swing, x, z):
    """궁합: +1 맞음, -1 반대, 0 보통. 레벨은 가운데 원에서만 보너스, 패널티 없음."""
    reg = region(x, z)
    if MATCH[reg] == swing:
        return 1
    if OPPOSITE.get(reg) == swing:
        return -1
    return 0
