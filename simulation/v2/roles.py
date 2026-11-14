"""
4단계: 능력치 역할 확인. 한 능력치만 50 → 70으로 올린 선수가 평균(50) 상대와 붙을 때 결과 (5.2절 v1 표와 비교).
사용: python3 roles.py [SCALE] [타석 수]
"""
import random
import sys
from collections import Counter

import config
from players import make_batter, make_pitcher
from plate import plate_appearance


def line(res, n):
    h = res["단타"] + res["2루타"] + res["3루타"] + res["홈런"]
    ab = n - res["볼넷"] - res["사구"]
    obp = (h + res["볼넷"] + res["사구"]) / n
    slg = (res["단타"] + 2 * res["2루타"] + 3 * res["3루타"] + 4 * res["홈런"]) / ab
    return {"타율": h / ab, "출루율": obp, "장타율": slg, "OPS": obp + slg,
            "삼진": res["삼진"] / n, "볼넷": res["볼넷"] / n, "홈런": res["홈런"] / n}


def run(side, stat, value, n, seed=3):
    rng = random.Random(seed)
    pitchers = [make_pitcher(f"P{i}", rng=rng) for i in range(200)]
    batter = make_batter("B")
    if side == "타자":
        setattr(batter, stat, value)
    res = Counter()
    for i in range(n):
        p = pitchers[i % len(pitchers)]
        if side == "투수":
            setattr(p, stat, value)
        p.pitches_today = 0
        res[plate_appearance(batter, p, 50, rng)[0]] += 1
        if side == "투수":
            setattr(p, stat, 50)
    return line(res, n)


ROWS = [("타자", "con", "정확"), ("타자", "pow", "파워"), ("타자", "eye", "선구"), ("타자", "spd", "주루"),
        ("투수", "vel", "구속"), ("투수", "stuff", "구위"), ("투수", "brk", "변화"), ("투수", "ctl", "제구")]

if __name__ == "__main__":
    config.SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    for m in ("pitcher_ai", "batter_ai", "judge", "batted_ball"):
        __import__(m).SCALE = config.SCALE
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 60000
    base = run("타자", "con", 50, n)
    print(f"SCALE {config.SCALE}  평균(50): " + " ".join(f"{k} {v:.3f}" for k, v in base.items()))
    for side, stat, name in ROWS:
        s = run(side, stat, 70, n)
        print(f"{side} {name} 70: " + " ".join(f"{k} {v:.3f}" for k, v in s.items()))
