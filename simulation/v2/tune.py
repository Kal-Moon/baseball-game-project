"""
조정값 자동 찾기 (좌표 탐색). 결과 목표(KBO)는 무겁게, 공 단위 출발점(MLB)은 가볍게 맞춤.
사용: python3 tune.py [타석 수] [반복]
"""
import json
import sys

import random

import config
from step1 import run

# 목표, 허용 폭(이만큼 벗어나면 손실 1), 무게
GOALS = {
    "삼진": (0.194, 0.005, 3), "볼넷": (0.092, 0.005, 3), "사구": (0.0143, 0.002, 2),
    "홈런": (0.0235, 0.002, 3), "BABIP": (0.318, 0.006, 3), "2루타/안타": (0.172, 0.015, 1),
    "타석당 투구": (3.88, 0.10, 2), "존 안": (0.506, 0.02, 1), "존 안 스윙": (0.669, 0.03, 1),
    "체이스": (0.282, 0.03, 2), "존 안 헛스윙/스윙": (0.173, 0.03, 0.5), "존 밖 헛스윙/스윙": (0.447, 0.04, 0.5),
    "당겨침": (0.442, 0.02, 3), "존 안 파울/스윙": (0.420, 0.03, 1), "존 밖 파울/스윙": (0.341, 0.03, 0.5),
}
KNOBS = {  # 이름: 한 번에 움직이는 폭
    "aim_shift": 0.03, "swing_in": 0.1, "swing_out": 0.1, "chase_dist": 0.02, "c0": 0.1,
    "out_pen": 0.02, "f0": 0.1, "ev0": 1.0, "la0": 1.5, "body_x": 0.5, "dir_bias": 0.1,
    "mistake": 0.004, "c_q": 0.1,
    "la_sd": 1.5, "ev_sd": 1.0, "f_q": 0.1, "t_sd": 0.1, "dir_x": 0.1,
    "two_strike_cut": 0.1, "hit_mult": 0.01,
}


def loss(s):
    return sum(w * ((s[k] - t) / tol) ** 2 for k, (t, tol, w) in GOALS.items())


def main(n=30000, rounds=6, start=None):
    P = config.P
    if start:
        P.update(start)
    rng = random.Random(5)
    best = loss(run(n))
    print("시작 손실", round(best, 2))
    for r in range(rounds):
        for k, step in KNOBS.items():
            for sgn in (1, -1):
                improved = True
                while improved:
                    old = P[k]
                    P[k] = old + sgn * step
                    l = loss(run(n))
                    improved = l < best
                    if improved:
                        best = l
                    else:
                        P[k] = old
        # 여러 값을 한꺼번에 조금씩 흔들어 보기 (한 값씩으로는 못 빠져나오는 곳)
        for _ in range(60):
            old = dict(P)
            for k, step in KNOBS.items():
                P[k] = P[k] + rng.choice((-1, 0, 0, 1)) * step
            l = loss(run(n))
            if l < best:
                best = l
            else:
                P.clear(); P.update(old)
        print(f"반복 {r + 1}: 손실 {best:.2f}")
    print(json.dumps({k: round(P[k], 4) for k in KNOBS}, ensure_ascii=False))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    start = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    main(n, rounds, start)
