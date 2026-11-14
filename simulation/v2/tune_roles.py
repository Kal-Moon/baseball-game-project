"""
4단계 조정: 능력치 효과 크기(k_*)를 v1 역할 표(5.2절, 배율 1.0에서 50 → 70)에 맞춤.
리그 평균(모두 50)에는 영향이 없음 (능력치 차이가 0이라).
"""
import json
import random
import sys

import config
import roles

# v1 결과 (baseball_sim.py exp2·exp3, SCALE 1.0, 10만 타석)
V1 = {
    ("타자", "con"): {"타율": 0.326, "출루율": 0.394, "장타율": 0.479, "삼진": 0.107, "볼넷": 0.089, "홈런": 0.024},
    ("타자", "pow"): {"타율": 0.296, "출루율": 0.368, "장타율": 0.524, "삼진": 0.180, "볼넷": 0.090, "홈런": 0.047},
    ("타자", "eye"): {"타율": 0.256, "출루율": 0.378, "장타율": 0.380, "삼진": 0.180, "볼넷": 0.153, "홈런": 0.019},
    ("타자", "spd"): {"타율": 0.278, "출루율": 0.352, "장타율": 0.430, "삼진": 0.179, "볼넷": 0.090, "홈런": 0.022},
    ("투수", "vel"): {"타율": 0.228, "출루율": 0.306, "장타율": 0.334, "삼진": 0.265, "볼넷": 0.089, "홈런": 0.017},
    ("투수", "stuff"): {"타율": 0.229, "출루율": 0.307, "장타율": 0.334, "삼진": 0.195, "볼넷": 0.089, "홈런": 0.017},
    ("투수", "ctl"): {"타율": 0.258, "출루율": 0.305, "장타율": 0.377, "삼진": 0.183, "볼넷": 0.051, "홈런": 0.019},
    ("투수", "brk"): {"타율": 0.239, "출루율": 0.316, "장타율": 0.325, "삼진": 0.204, "볼넷": 0.089, "홈런": 0.014},
}
# v1 기준선과 v2 기준선이 조금 달라서 "변화량"을 맞춤
V1_BASE = {"타율": 0.260, "출루율": 0.336, "장타율": 0.389, "삼진": 0.178, "볼넷": 0.090, "홈런": 0.022}
TOL = {"타율": 0.008, "출루율": 0.008, "장타율": 0.012, "삼진": 0.008, "볼넷": 0.006, "홈런": 0.003}
KNOBS = {"k_pow_ev": 0.3, "k_acc": 0.05, "k_acc_neg": 0.03, "k_eye_chase": 0.05, "k_eye_t": 0.03, "k_spd": 0.03,
         "k_vel_t": 0.03, "k_brk_match": 0.05, "k_ctl_miss": 0.03, "k_ctl_mistake": 0.1, "k_dfn": 0.02}


def evaluate(n):
    base = roles.run("타자", "con", 50, n)
    out = {}
    for (side, stat) in V1:
        out[(side, stat)] = roles.run(side, stat, 70, n)
    return base, out


def loss(base, out):
    l = 0
    for key, v1 in V1.items():
        for m, t in v1.items():
            want = t - V1_BASE[m]
            got = out[key][m] - base[m]
            l += ((got - want) / TOL[m]) ** 2
    return l


def main(n, rounds):
    config.SCALE = 1.0
    for m in ("pitcher_ai", "batter_ai", "judge", "batted_ball"):
        __import__(m).SCALE = 1.0
    P = config.P
    rng = random.Random(4)
    best = loss(*evaluate(n))
    print("시작 손실", round(best, 1), flush=True)
    for r in range(rounds):
        for k, step in KNOBS.items():
            for sgn in (1, -1):
                improved = True
                while improved:
                    old = P[k]
                    P[k] = max(0.0, old + sgn * step)
                    l = loss(*evaluate(n))
                    improved = l < best
                    if improved:
                        best = l
                    else:
                        P[k] = old
        for _ in range(20):
            old = dict(P)
            for k, step in KNOBS.items():
                P[k] = max(0.0, P[k] + rng.choice((-1, 0, 0, 1)) * step)
            l = loss(*evaluate(n))
            if l < best:
                best = l
            else:
                P.clear()
                P.update(old)
        print(f"반복 {r + 1}: 손실 {best:.1f}", flush=True)
    print(json.dumps({k: round(P[k], 4) for k in KNOBS}, ensure_ascii=False))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 25000, int(sys.argv[2]) if len(sys.argv) > 2 else 3)
