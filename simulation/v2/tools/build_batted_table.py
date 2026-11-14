"""
Savant 인플레이 타구 원자료(CSV 여러 개) → 타구 결과 표(batted_table.py) 만들기.
사용: python3 -I build_batted_table.py <출력 파일> <csv 파일들...>
표: 속도(5마일 칸) × 각도(10도 칸) × 방향(당겨침·가운데·밀어침) → [타구 수, 단타, 2루타, 3루타, 홈런 비율]
자료: MLB 2025 정규시즌 (Baseball Savant, type=details, hfPR=hit_into_play)
"""
import csv, math, sys
from collections import defaultdict

H = {"single": 0, "double": 1, "triple": 2, "home_run": 3}


def ev_bin(v):
    return max(55, min(115, int(v // 5) * 5))  # 55 = 60 미만, 115 = 115 이상


def la_bin(a):
    return max(-30, min(70, int(math.floor(a / 10)) * 10))  # -30 = -20 미만, 70 = 70 이상


def dir_bin(r):
    try:
        x = float(r["hc_x"]) - 125.42
        y = 198.27 - float(r["hc_y"])
    except ValueError:
        return None
    ang = math.degrees(math.atan2(x, y))
    if r["stand"] == "L":
        ang = -ang
    return 0 if ang < -15 else (1 if ang <= 15 else 2)  # 0 당겨침, 1 가운데, 2 밀어침


cnt = defaultdict(lambda: [0, 0, 0, 0, 0])
total = 0
for f in sys.argv[2:]:
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if not r["launch_speed"] or not r["launch_angle"]:
            continue
        d = dir_bin(r)
        if d is None:
            continue
        k = (ev_bin(float(r["launch_speed"])), la_bin(float(r["launch_angle"])), d)
        c = cnt[k]
        c[0] += 1
        if r["events"] in H:
            c[1 + H[r["events"]]] += 1
        total += 1

with open(sys.argv[1], "w", encoding="utf-8") as out:
    out.write('"""자동 생성 파일 (tools/build_batted_table.py). MLB 2025 정규시즌 인플레이 타구, Baseball Savant.\n')
    out.write(f'키: (속도 칸 마일, 각도 칸 도, 방향 0당겨침/1가운데/2밀어침) → (타구 수, 단타, 2루타, 3루타, 홈런 비율). 전체 {total}개"""\n')
    out.write("BATTED = {\n")
    for k in sorted(cnt):
        n, s, d2, t3, hr = cnt[k]
        out.write(f"    {k}: ({n}, {s/n:.4f}, {d2/n:.4f}, {t3/n:.4f}, {hr/n:.4f}),\n")
    out.write("}\n")
print("cells", len(cnt), "rows", total)
