"""
2단계: 주자·수비·주루·경기·시즌.
첫 v2에서 뺀 것 (계획대로): 도루·견제·번트, 고의사구, 직접 수비 기회, 핫·콜드존, 특수 구종, 정신력.
"""
import random
import statistics
from collections import Counter
from dataclasses import dataclass, field

from config import P, SCALE
from players import make_batter, make_pitcher
from plate import plate_appearance

POS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]


@dataclass
class Team:
    name: str
    lineup: list          # 9명, POS 순서대로 수비 위치
    rotation: list
    bullpen: list
    rot_idx: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    stat: Counter = field(default_factory=Counter)

    def fielder(self, la, d):
        """그 타구를 처리한 야수의 수비 능력치. 땅볼은 내야, 그 밖은 외야. 방향 0 당겨침 → 3루·유격·좌익 쪽."""
        L = {p: b for p, b in zip(POS, self.lineup)}
        if la < 10:
            group = [["3B", "SS"], ["SS", "2B"], ["2B", "1B"]][d]
        elif la < 50:
            group = [["LF"], ["CF"], ["RF"]][d]
        else:
            group = [["3B", "SS"], ["SS", "2B"], ["2B", "1B"]][d]  # 내야 뜬공
        return statistics.mean(L[g].dfn for g in group)


def make_team(name, mean=50, sd=0, rng=random):
    lineup = [make_batter(f"{name}-{p}", mean, sd, rng) for p in POS]
    rotation = [make_pitcher(f"{name}-SP{i+1}", mean, sd, rng, sta=rng.gauss(95, 8)) for i in range(5)]
    bullpen = [make_pitcher(f"{name}-RP{i+1}", mean, sd, rng, sta=rng.gauss(30, 5)) for i in range(7)]
    return Team(name, lineup, rotation, bullpen)


def _spd(runner):
    return (runner.spd - 50) / 10 * SCALE * P["k_spd"]


class HalfInning:
    def __init__(self, bat, fld, pitcher_getter, rng, stat):
        self.bat, self.fld, self.get_p, self.rng, self.st = bat, fld, pitcher_getter, rng, stat
        self.bases = [None, None, None]
        self.outs = 0
        self.runs = 0

    def score(self, n=1):
        self.runs += n
        self.st["R"] += n

    def wild_pitch(self):
        """폭투·포일: 주자 모두 한 베이스."""
        b = self.bases
        if not any(b):
            return
        if b[2]:
            self.score()
        self.bases = [None, b[0], b[1]]
        self.st["WP"] += 1

    def walk(self, batter):
        b = self.bases
        if b[0]:
            if b[1]:
                if b[2]:
                    self.score()
                b[2] = b[1]
            b[1] = b[0]
        b[0] = batter

    def hit(self, batter, kind):
        b, r = self.bases, self.rng
        if kind == "홈런":
            self.score(1 + sum(1 for x in b if x))
            self.bases = [None, None, None]
            return
        if kind == "3루타":
            self.score(sum(1 for x in b if x))
            self.bases = [None, None, batter]
            return
        if kind == "2루타":
            n = (1 if b[2] else 0) + (1 if b[1] else 0)
            new3 = None
            if b[0]:
                if r.random() < P["adv_2b_r1_home"] + _spd(b[0]):
                    n += 1
                else:
                    new3 = b[0]
            self.score(n)
            self.bases = [None, batter, new3]
            return
        # 단타
        n = 1 if b[2] else 0
        new = [batter, None, None]
        if b[1]:
            if r.random() < P["adv_1b_r2_home"] + _spd(b[1]):
                n += 1
            else:
                new[2] = b[1]
        if b[0]:
            if new[2] is None and r.random() < P["adv_1b_r1_3b"] + _spd(b[0]):
                new[2] = b[0]
            else:
                new[1] = b[0]
        self.score(n)
        self.bases = new

    def out_in_play(self, batter, la, ev):
        b, r = self.bases, self.rng
        if r.random() < P["error"]:            # 실책 출루: 주자 한 베이스
            self.st["E"] += 1
            if b[2]:
                self.score()
            self.bases = [batter, b[0], b[1]]
            return
        if la < 10:                              # 땅볼
            if b[0] and self.outs < 2 and r.random() < P["dp_prob"] - _spd(batter):
                self.outs += 2
                self.st["GIDP"] += 1
                if self.outs < 3:
                    if b[2]:
                        self.score()
                    self.bases = [None, None, b[1]] if b[1] else [None, None, None]
                return
            self.outs += 1
            if self.outs < 3:
                if b[2] and r.random() < P["gb_adv"]:
                    self.score()
                    b[2] = None
                if b[1] and not b[2] and r.random() < P["gb_adv"]:
                    b[2], b[1] = b[1], None
                if b[0]:                         # 1루 주자는 포스 → 2루로 (타자 아웃)
                    if not b[1]:
                        b[1], b[0] = b[0], None
            return
        self.outs += 1
        if 10 <= la < 50 and ev > 80 and self.outs < 3:   # 외야로 간 뜬공·라인드라이브
            if b[2] and r.random() < P["sf_prob"] + _spd(b[2]):
                self.score()
                b[2] = None
                self.st["SF"] += 1
            if b[1] and not b[2] and r.random() < P["fly_r2_adv"]:
                b[2], b[1] = b[1], None

    def try_steal(self):
        """2루 도루만 (첫 v2). 시간 싸움(3.1절): 성공률 = 리그 평균 + (주루 − 포수 송구), 상한·하한.
        AI는 성공률이 기준 이상일 때만, 주루가 높을수록 자주 시도."""
        b, r = self.bases, self.rng
        if not b[0] or b[1] or self.outs == 2:
            return
        runner = b[0]
        catcher = self.fld.lineup[0]
        gap = (runner.spd - catcher.arm) / 10 * SCALE
        p_succ = min(P["sb_cap"], max(0.3, P["sb_base"] + P["k_sb"] * gap))
        if p_succ < P["sb_min_try"]:
            return
        if r.random() >= P["sb_try"] * (1 + P["k_sb_try"] * gap):
            return
        self.st["SBA"] += 1
        if r.random() < p_succ:
            self.st["SB"] += 1
            self.bases = [None, runner, b[2]]
        else:
            self.bases = [None, None, b[2]]
            self.outs += 1

    def play(self, order_idx, walkoff_need=None):
        """이닝 진행. order_idx: 타순 시작. 끝내기면 walkoff_need 점에 닿을 때 끝."""
        while self.outs < 3:
            self.try_steal()
            if self.outs >= 3:
                break
            batter = self.bat.lineup[order_idx % 9]
            order_idx += 1
            pitcher = self.get_p(self)
            res, ball = plate_appearance(batter, pitcher, self.fld.fielder, self.rng,
                                         wp_cb=self.wild_pitch if any(self.bases) else None)
            st = self.st
            st["PA"] += 1
            if res == "삼진":
                st["SO"] += 1
                st["AB"] += 1
                self.outs += 1
            elif res in ("볼넷", "사구"):
                st["BB" if res == "볼넷" else "HBP"] += 1
                self.walk(batter)
            elif res == "아웃":
                ev, la, d = ball
                before = st["SF"]
                self.out_in_play(batter, la, ev)
                if st["SF"] == before:
                    st["AB"] += 1
            else:
                st["AB"] += 1
                st["H"] += 1
                st[{"단타": "1B", "2루타": "2B", "3루타": "3B", "홈런": "HR"}[res]] += 1
                self.hit(batter, res)
            if walkoff_need is not None and self.runs >= walkoff_need:
                break
        return order_idx


class Staff:
    """투수 운영: 선발은 투구 수가 체력(한계)에 닿으면 교체, 불펜은 1이닝 또는 한계."""

    def __init__(self, team, day):
        self.team = team
        self.cur = team.rotation[team.rot_idx % 5]
        team.rot_idx += 1
        self.cur.pitches_today = 0
        self.used = {id(self.cur)}
        self.inning_started = 0
        self.day = day

    def get(self, half, inning):
        p = self.cur
        tired = p.pitches_today >= p.sta
        reliever_done = p in self.team.bullpen and inning > self.inning_started and half.outs == 0
        if tired or reliever_done:
            fresh = [r for r in self.team.bullpen if id(r) not in self.used and r.rest_until <= self.day]
            if not fresh:
                fresh = [r for r in self.team.bullpen if id(r) not in self.used] or self.team.bullpen
            nxt = fresh[0]
            nxt.pitches_today = 0
            self.used.add(id(nxt))
            self.cur = nxt
            self.inning_started = inning
        return self.cur

    def finish(self):
        for r in self.team.bullpen:
            if id(r) in self.used:
                r.rest_until = self.day + (2 if r.pitches_today > 25 else 1)
                # 쓴 불펜은 뒤로 보내서 고르게 씀
        self.team.bullpen.sort(key=lambda r: r.rest_until)


def play_game(home, away, rng, day=0, max_inn=12):
    hs, as_ = Staff(home, day), Staff(away, day)
    score = {home.name: 0, away.name: 0}
    idx = {home.name: 0, away.name: 0}
    inn = 1
    while True:
        # 초: 원정 공격
        h = HalfInning(away, home, lambda hf, i=inn: hs.get(hf, i), rng, away.stat)
        idx[away.name] = h.play(idx[away.name])
        score[away.name] += h.runs
        if inn >= 9 and score[home.name] > score[away.name]:
            break
        need = (score[away.name] - score[home.name] + 1) if inn >= 9 else None
        h = HalfInning(home, away, lambda hf, i=inn: as_.get(hf, i), rng, home.stat)
        idx[home.name] = h.play(idx[home.name], need)
        score[home.name] += h.runs
        if inn >= 9 and score[home.name] != score[away.name]:
            break
        if inn >= max_inn:
            break
        inn += 1
    for t in (home, away):
        t.stat["G"] += 1
    hs.finish()
    as_.finish()
    a, b = score[home.name], score[away.name]
    if a > b:
        home.wins += 1
        away.losses += 1
    elif b > a:
        away.wins += 1
        home.losses += 1
    else:
        home.ties += 1
        away.ties += 1
    return a, b


def season(teams, rng, games_per_pair=16):
    day = 0
    pairs = [(a, b) for i, a in enumerate(teams) for b in teams[i + 1:]]
    for g in range(games_per_pair):
        rng.shuffle(pairs)
        for k, (a, b) in enumerate(pairs):
            home, away = (a, b) if g % 2 == 0 else (b, a)
            play_game(home, away, rng, day)
            if k % 5 == 4:
                day += 1
        day += 1


def league_stats(teams):
    s = Counter()
    for t in teams:
        s.update(t.stat)
    pa, ab, h = s["PA"], s["AB"], s["H"]
    obp = (h + s["BB"] + s["HBP"]) / (ab + s["BB"] + s["HBP"] + s["SF"])
    slg = (s["1B"] + 2 * s["2B"] + 3 * s["3B"] + 4 * s["HR"]) / ab
    return {
        "타율": h / ab, "출루율": obp, "장타율": slg, "삼진": s["SO"] / pa, "볼넷": s["BB"] / pa,
        "사구": s["HBP"] / pa, "홈런": s["HR"] / pa, "BABIP": (h - s["HR"]) / (ab - s["SO"] - s["HR"] + s["SF"]),
        "2루타/안타": s["2B"] / h, "팀당 득점": s["R"] / s["G"], "병살/경기": s["GIDP"] / s["G"],
        "폭투·포일/경기": s["WP"] / s["G"], "실책/경기": s["E"] / s["G"],
        "도루 시도/경기": s["SBA"] / s["G"], "도루 성공률": s["SB"] / max(1, s["SBA"]),
    }


TARGET2 = {"타율": (0.269, 0.005), "출루율": (0.346, 0.005), "장타율": (0.404, 0.005), "삼진": (0.194, 0.005),
           "볼넷": (0.092, 0.005), "사구": (0.0143, 0.002), "홈런": (0.0235, 0.002), "팀당 득점": (5.06, 0.2)}


def run_season(seed=1, mean=50, sd=0, n_teams=10):
    rng = random.Random(seed)
    teams = [make_team(f"T{i}", mean, sd, rng) for i in range(n_teams)]
    season(teams, rng)
    return teams


if __name__ == "__main__":
    import sys
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    allt = []
    for sd in range(seeds):
        allt += run_season(seed=100 + sd)
    s = league_stats(allt)
    for k, v in s.items():
        t = TARGET2.get(k)
        mark = "" if t is None else ("  ✅" if abs(v - t[0]) <= t[1] else "  ❌") + f" 목표 {t[0]}"
        print(f"{k:14s} {v:.3f}{mark}")
