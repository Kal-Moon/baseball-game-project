"""
4단계: 난이도(영향력 배율 SCALE) 확인. 5.3절 v1과 같은 조건:
AI 9팀은 팀 평균 50±5, 내 팀은 50 + (0, 5, 10, 15). 선수 능력치는 팀 평균 ± 8.
사용: python3 difficulty.py [SCALE] [시즌 수]
"""
import random
import sys

import config
from game import make_team, season


def trial(offset, seed):
    rng = random.Random(seed)
    teams = [make_team("ME", 50 + offset, 8, rng)]
    teams += [make_team(f"AI{i}", 50 + rng.uniform(-5, 5), 8, rng) for i in range(9)]
    season(teams, rng)
    pct = [t.wins / max(1, t.wins + t.losses) for t in teams]
    return pct[0], max(pct) - min(pct)


if __name__ == "__main__":
    config.SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.35
    for m in ("pitcher_ai", "batter_ai", "judge", "batted_ball", "game"):
        __import__(m).SCALE = config.SCALE
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    row = []
    spread = []
    for off in (0, 5, 10, 15):
        r = [trial(off, 1000 + 37 * s + off) for s in range(n)]
        row.append(sum(a for a, _ in r) / n)
        spread += [b for _, b in r]
    print(f"SCALE {config.SCALE}: 내 팀 +0 {row[0]:.3f}  +5 {row[1]:.3f}  +10 {row[2]:.3f}  +15 {row[3]:.3f}"
          f"  1위-꼴찌 차 {sum(spread) / len(spread):.3f}")
