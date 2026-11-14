"""
1단계 확인: 공 하나 + 타석 (주자 없이). 평균 능력치(50) 타자·투수로 타석을 많이 돌려 목표와 비교.
사용: python3 step1.py [타석 수]
"""
import random
import sys
from collections import Counter

from players import make_batter, make_pitcher
from plate import plate_appearance

# 5.4절 목표 (KBO 2024~2026) + 공 단위 출발점 (MLB 2025)
TARGET = {"삼진": 0.194, "볼넷": 0.092, "사구": 0.0143, "홈런": 0.0235, "BABIP": 0.318,
          "2루타/안타": 0.172, "타석당 투구": 3.88, "존 안": 0.506, "존 안 스윙": 0.669, "체이스": 0.282,
          "강한 타구": 0.411, "당겨침": 0.442}


def run(n=40000, seed=1, params=None):
    if params:
        import config
        config.P.update(params)
    rng = random.Random(seed)
    pitchers = [make_pitcher(f"P{i}", rng=rng) for i in range(200)]
    batter = make_batter("B")
    res = Counter()
    log = Counter()
    for i in range(n):
        p = pitchers[i % len(pitchers)]
        p.pitches_today = 0
        res[plate_appearance(batter, p, 50, rng, log)[0]] += 1
    return stats(res, log, n)


def stats(res, log, n):
    hits = res["단타"] + res["2루타"] + res["3루타"] + res["홈런"]
    ab = n - res["볼넷"] - res["사구"]
    bip_nohr = ab - res["삼진"] - res["홈런"]
    zone = log["zone"]
    out = log["pitches"] - zone
    bip = log["b_in"] + log["b_out"]
    return {
        "삼진": res["삼진"] / n, "볼넷": res["볼넷"] / n, "사구": res["사구"] / n, "홈런": res["홈런"] / n,
        "BABIP": (hits - res["홈런"]) / bip_nohr, "2루타/안타": res["2루타"] / max(hits, 1),
        "타율": hits / ab, "출루율": (hits + res["볼넷"] + res["사구"]) / n,
        "장타율": (res["단타"] + 2 * res["2루타"] + 3 * res["3루타"] + 4 * res["홈런"]) / ab,
        "타석당 투구": log["pitches"] / n, "존 안": zone / log["pitches"],
        "존 안 스윙": log["swing_in"] / zone, "체이스": log["swing_out"] / out,
        "존 안 헛스윙/스윙": log["w_in"] / max(log["swing_in"], 1),
        "존 밖 헛스윙/스윙": log["w_out"] / max(log["swing_out"], 1),
        "존 안 파울/스윙": log["f_in"] / max(log["swing_in"], 1),
        "존 밖 파울/스윙": log["f_out"] / max(log["swing_out"], 1),
        "강한 타구": log["hard"] / bip, "평균 타구 속도": log["ev"] / bip, "평균 각도": log["la"] / bip,
        "당겨침": log["dir0"] / bip, "가운데": log["dir1"] / bip, "밀어침": log["dir2"] / bip,
    }


def show(s):
    for k, v in s.items():
        t = TARGET.get(k)
        fmt = (lambda a: f"{a:.3f}") if v < 10 else (lambda a: f"{a:.1f}")
        print(f"{k:12s} {fmt(v):>7s}" + (f"   목표 {fmt(t)}" if t is not None else ""))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    show(run(n))
