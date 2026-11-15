"""10개 구단 스타일이 결과로 다르게 보이는지 확인 (2.1절 초안). 팀 평균 50, 선수 ±8."""
import random
from collections import Counter
from game import make_team, season

STYLES = {  # (타자 조정, 선발 조정, 불펜 조정)
    "청주 거포": ({"pow": 6, "con": -3, "spd": -3}, {}, {}),
    "전주 선발": ({"con": -3, "pow": -3, "eye": -3, "spd": -3}, {"vel": 6, "stuff": 6}, {}),
    "제주 발야구": ({"spd": 8, "dfn": 3, "pow": -6}, {}, {}),
    "울산 출루": ({"eye": 6, "con": 3, "pow": -4}, {}, {}),
    "포항 불펜": ({}, {"vel": -4, "stuff": -4, "ctl": -4, "brk": -4}, {"vel": 6, "stuff": 6, "ctl": 6, "brk": 6}),
    "춘천 수비": ({"dfn": 6, "arm": 6, "pow": -4}, {"ctl": 3}, {"ctl": 3}),
    "천안 균형": ({}, {}, {}),
    "여수 변화구": ({}, {"brk": 6, "vel": -4}, {"brk": 6, "vel": -4}),
    "안동 원맨": ({"con": -2, "pow": -2, "eye": -2, "spd": -2}, {"vel": -2, "stuff": -2, "ctl": -2, "brk": -2}, {}),
    "세종 제구": ({"eye": 2}, {"ctl": 6, "vel": -3}, {"ctl": 6, "vel": -3}),
}


def styled(name, rng):
    t = make_team(name, 50, 8, rng)
    bat, sp, rp = STYLES[name]
    for b in t.lineup:
        for k, v in bat.items():
            setattr(b, k, getattr(b, k) + v)
    for p in t.rotation:
        for k, v in sp.items():
            setattr(p, k, getattr(p, k) + v)
    for p in t.bullpen:
        for k, v in rp.items():
            setattr(p, k, getattr(p, k) + v)
    if name == "안동 원맨":
        t.lineup[3].con += 20; t.lineup[3].pow += 20; t.lineup[3].eye += 20; t.lineup[3].spd += 20
    return t


if __name__ == "__main__":
    tot = {n: Counter() for n in STYLES}
    for s in range(4):
        rng = random.Random(800 + s)
        teams = [styled(n, rng) for n in STYLES]
        season(teams, rng)
        for t in teams:
            tot[t.name].update(t.stat)
            tot[t.name]["W"] += t.wins
            tot[t.name]["L"] += t.losses
    print("구단          승률   홈런/경기 도루/경기 삼진% 볼넷%  득점/경기")
    for n, s in tot.items():
        print(f"{n:10s} {s['W']/(s['W']+s['L']):.3f}   {s['HR']/s['G']:.2f}     {s['SB']/s['G']:.2f}     "
              f"{s['SO']/s['PA']*100:4.1f}  {s['BB']/s['PA']*100:4.1f}   {s['R']/s['G']:.2f}")
