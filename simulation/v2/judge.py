"""5.5절 5: 헛스윙 / 파울 / 인플레이 판정. 직접 플레이와 같이 쓰는 함수 (입력: 타이밍·스윙 종류)"""
from config import P, SCALE
from batter_ai import inv_logit, out_dist

TIMING_SCORE = {"완벽": 1.0, "좋음": 0.6, "빠름": 0.0, "늦음": 0.0, "너무 빠름": -2.0, "너무 늦음": -2.0}


def quality(batter, pitcher, t_grade, comp, x, z):
    """품질: 타이밍 + 궁합 + (정확 − 변화) − 존 밖 거리."""
    return (TIMING_SCORE[t_grade]
            + P["compat"] * comp
            + P["k_acc"] * (batter.con - pitcher.brk) / 10 * SCALE
            - P["out_pen"] * out_dist(x, z))


def judge(q, t_grade, rng):
    """맞힘 → 페어/파울. 너무 빠름·너무 늦음은 거의 헛스윙이고 맞아도 대부분 파울."""
    if rng.random() >= inv_logit(P["c0"] + P["c_q"] * q):
        return "헛스윙"
    if rng.random() < inv_logit(P["f0"] + P["f_q"] * q):
        return "인플레이"
    return "파울"
