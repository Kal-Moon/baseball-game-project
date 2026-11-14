"""5.5절 5: 헛스윙 / 파울 / 인플레이 판정. 직접 플레이와 같이 쓰는 함수 (입력: 타이밍·스윙 종류)"""
from config import P, SCALE
from batter_ai import inv_logit, out_dist

TIMING_SCORE = {"완벽": 1.0, "좋음": 0.6, "빠름": 0.0, "늦음": 0.0, "너무 빠름": -2.0, "너무 늦음": -2.0}


def quality(batter, pitcher, t_grade, comp, x, z, with_acc=True):
    """품질: 타이밍 + 궁합 + (정확 − 변화) − 존 밖 거리.
    with_acc=False: 타구 속도용. 정확은 "빗나간 스윙을 덜 나쁘게"(맞힘·페어)라 타구 속도에는 넣지 않음 (4단계, 2026-11-14)."""
    gap = (batter.con - pitcher.brk) / 10 * SCALE
    # 양수·음수 쪽 계수를 따로, 음수 쪽(변화 > 정확)을 더 작게 (6장 보류 목록 "정확의 계수와 상한")
    acc = (P["k_acc"] if gap > 0 else P["k_acc_neg"]) * gap if with_acc else 0.0
    return (TIMING_SCORE[t_grade]
            + P["compat"] * comp
            + acc
            - P["out_pen"] * out_dist(x, z))


def judge(q, t_grade, rng, strikes=0):
    """맞힘 → 페어/파울. 너무 빠름·너무 늦음은 거의 헛스윙이고 맞아도 대부분 파울.
    2스트라이크 뒤에는 커트(일부러 파울)가 늘어남 (1단계 결정, 2026-11-14)."""
    if rng.random() >= inv_logit(P["c0"] + P["c_q"] * q):
        return "헛스윙"
    cut = P["two_strike_cut"] if strikes == 2 else 0.0
    if rng.random() < inv_logit(P["f0"] + P["f_q"] * q - cut):
        return "인플레이"
    return "파울"
