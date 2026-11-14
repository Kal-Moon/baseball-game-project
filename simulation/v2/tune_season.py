"""
2단계 조정: 시즌 전체(주자·교체 포함)로 5.4절 KBO 목표에 맞춤. 공 단위 출발점(MLB)은 가볍게.
사용: python3 tune_season.py [시즌 수] [반복] [시작값 JSON]
"""
import json
import random
import sys
from collections import Counter

import config
from game import run_season, league_stats

GOALS = {  # 목표, 허용 폭, 무게
    "타율": (0.269, 0.005, 3), "출루율": (0.346, 0.005, 3), "장타율": (0.404, 0.005, 3),
    "삼진": (0.194, 0.005, 3), "볼넷": (0.092, 0.005, 3), "사구": (0.0143, 0.002, 2),
    "홈런": (0.0235, 0.002, 3), "팀당 득점": (5.06, 0.2, 3), "2루타/안타": (0.172, 0.015, 1),
}
KNOBS = {
    "aim_shift": 0.02, "swing_in": 0.1, "swing_out": 0.1, "c0": 0.1, "f0": 0.1, "ev0": 0.5,
    "la0": 1.0, "body_x": 0.5, "hit_mult": 0.01, "two_strike_cut": 0.1, "adv_1b_r2_home": 0.05,
}


def evaluate(n_seasons):
    teams = []
    for s in range(n_seasons):
        teams += run_season(seed=500 + s)
    return league_stats(teams)


def loss(s):
    return sum(w * ((s[k] - t) / tol) ** 2 for k, (t, tol, w) in GOALS.items())


def main(n=2, rounds=3, start=None):
    P = config.P
    if start:
        P.update(start)
    rng = random.Random(9)
    best = loss(evaluate(n))
    print("시작 손실", round(best, 2), flush=True)
    for r in range(rounds):
        for k, step in KNOBS.items():
            for sgn in (1, -1):
                improved = True
                while improved:
                    old = P[k]
                    P[k] = old + sgn * step
                    l = loss(evaluate(n))
                    improved = l < best
                    if improved:
                        best = l
                    else:
                        P[k] = old
        for _ in range(30):
            old = dict(P)
            for k, step in KNOBS.items():
                P[k] += rng.choice((-1, 0, 0, 1)) * step
            l = loss(evaluate(n))
            if l < best:
                best = l
            else:
                P.clear()
                P.update(old)
        print(f"반복 {r + 1}: 손실 {best:.2f}", flush=True)
    print(json.dumps({k: round(P[k], 4) for k in KNOBS}, ensure_ascii=False))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    start = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    main(n, rounds, start)
