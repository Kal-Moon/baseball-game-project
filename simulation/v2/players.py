"""선수 (능력치와 구종)"""
import random
from dataclasses import dataclass, field

from tables import PITCHES, GRADE_PROB, GRADE_USE, N_PITCHES


@dataclass
class Batter:
    name: str
    con: float = 50  # 정확
    pow: float = 50  # 파워
    eye: float = 50  # 선구
    spd: float = 50  # 주루
    dfn: float = 50  # 수비
    arm: float = 50  # 송구


@dataclass
class Pitch:
    name: str
    family: str
    ratio: float   # 포심 대비 속도 비율
    grade: str     # 구종 등급 S~D (제구만)
    use: float     # 구사율 가중치


@dataclass
class Pitcher:
    name: str
    vel: float = 50    # 구속
    stuff: float = 50  # 구위
    ctl: float = 50    # 제구
    brk: float = 50    # 변화
    sta: float = 95    # 체력 (투구 수 한계)
    pitches: list = field(default_factory=list)
    pitches_today: int = 0


def _pick(weights, rng):
    r = rng.random() * sum(weights.values())
    for k, w in weights.items():
        r -= w
        if r <= 0:
            return k
    return k


def make_repertoire(rng=random):
    """구종 수를 먼저 뽑고, 패스트볼 계열 1개를 넣은 뒤 나머지를 한국 리그 확률로 (2.3절)."""
    n = _pick(N_PITCHES, rng)
    fb = {k: v[3] for k, v in PITCHES.items() if v[0] == "패스트볼"}
    names = [_pick(fb, rng)]
    while len(names) < n:
        rest = {k: v[3] for k, v in PITCHES.items() if k not in names}
        names.append(_pick(rest, rng))
    out = []
    for nm in names:
        fam, ratio, spread, _, gkind = PITCHES[nm]
        r = ratio if spread == 0 else min(ratio + spread, max(ratio - spread, rng.gauss(ratio, spread / 2)))
        g = _pick(GRADE_PROB[gkind], rng)
        out.append(Pitch(nm, fam, r, g, GRADE_USE[g]))
    return out


def make_pitcher(name, mean=50, sd=0, rng=random, sta=95):
    g = lambda: rng.gauss(mean, sd) if sd else mean
    return Pitcher(name, g(), g(), g(), g(), sta, make_repertoire(rng))


def make_batter(name, mean=50, sd=0, rng=random):
    g = lambda: rng.gauss(mean, sd) if sd else mean
    return Batter(name, g(), g(), g(), g(), g(), g())
