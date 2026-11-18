## 4단계 확인: 결과 표시 + 조절판 (화면 없이). docs/game-design.md 4.1절 표 4단계 "값 바꿔 결과 변화 확인".
## 실행: godot --headless --path prototype/batting --script res://tests/result_test.gd -- [타석 수, 기본 6000]
## 실제 화면 장면에 "보통 유저 흉내"(스윙 판단 = 5.5절 보통 유저, 터치 오차 표준편차 60ms 가정)로 터치를 넣어 친다.
## 주의: 흉내 유저는 공이 느려져도 더 잘 맞히지 않으므로, 선구·구속의 "시간" 효과는 여기서 결과로 안 나옴
##       (도착 시간이 바뀌는지만 확인). 사람 손으로는 시험판에서 확인.
extends SceneTree

const Params := preload("res://core/params.gd")
const Model := preload("res://core/batting_model.gd")

var fails := 0
var checks := 0


func ok(cond: bool, msg: String) -> void:
	checks += 1
	print(("  통과  " if cond else "  실패  ") + msg)
	if not cond: fails += 1


func play(scene, n_pa: int, seed: int) -> Dictionary:
	var user: Dictionary = Params.USERS["보통"]
	var urng := RandomNumberGenerator.new(); urng.seed = seed
	scene.model.rng.seed = seed            # 비교하는 경우끼리 같은 난수 (흔들림 줄이기)
	scene.pa_over = true
	for k in scene.tally: scene.tally[k] = 0
	var texts := {}
	while scene.tally["PA"] < n_pa:
		scene.next_pitch()
		var f = scene.flight
		var zone := Model.in_zone(f.target.x, f.target.y)
		var p_sw: float = user["zone_swing"] if zone else user["chase"] * (0.7 if absf(f.target.x) > 1.6 or absf(f.target.y) > 1.6 else 1.0)
		if scene.strikes == 2: p_sw = minf(0.95, p_sw + (0.15 if zone else 0.05))
		if urng.randf() < p_sw:
			scene.fake_now = f.arrive_usec + int(urng.randfn(0.0, 60.0) * 1000.0)
			var d := InputEventScreenTouch.new(); d.pressed = true; d.position = Vector2(640, 500)
			scene._input(d)
			var dirs := [Vector2.ZERO, Vector2(0, -120), Vector2(0, 120), Vector2(-150, 0), Vector2(150, 0)]
			var u := InputEventScreenTouch.new(); u.pressed = false; u.position = Vector2(640, 500) + dirs[urng.randi_range(0, 4)]
			scene._input(u)
		scene.fake_now = f.arrive_usec + 300_000
		scene.tick()
		if not scene.hit_info.is_empty():
			texts[scene.hit_info["text"]] = texts.get(scene.hit_info["text"], 0) + 1
	var t: Dictionary = scene.tally.duplicate()
	var avg: float = float(t["H"]) / t["AB"]
	var obp: float = float(t["H"] + t["BB"] + t["HBP"]) / t["PA"]
	var tb: int = t["H"] + t["2B"] + 2 * t["3B"] + 3 * t["HR"]
	return {"avg": avg, "obp": obp, "slg": float(tb) / t["AB"], "k": float(t["K"]) / t["PA"], "hr": float(t["HR"]) / t["PA"], "texts": texts}


func line(name: String, r: Dictionary) -> String:
	return "%-10s 타율 %.3f 출루 %.3f 장타 %.3f 삼진 %.1f%% 홈런 %.1f%%" % [name, r["avg"], r["obp"], r["slg"], 100 * r["k"], 100 * r["hr"]]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var N := int(args[0]) if args.size() > 0 else 6000
	var scene: Node2D = load("res://ui/at_bat.tscn").instantiate()
	root.add_child(scene)
	scene.fake_now = 0
	scene._ready()

	print("① 능력치를 바꿔 %d타석씩 (보통 유저 흉내)" % N)
	var base := play(scene, N, 1)
	print("  " + line("기본(모두 50)", base))
	var tx: Dictionary = base["texts"]
	var top := tx.keys(); top.sort_custom(func(a, b): return tx[a] > tx[b])
	print("  타구 글자 예: ", ", ".join(top.slice(0, 8).map(func(k): return "%s %d" % [k, tx[k]])))
	ok(base["avg"] > 0.15 and base["avg"] < 0.40, "기본 타율이 말이 되는 범위 (%.3f)" % base["avg"])
	var cases := [["con", 80, "정확 80", "avg", 1], ["pw", 80, "파워 80", "hr", 1], ["brk", 80, "변화 80", "slg", -1],
		["st", 80, "구위 80", "slg", -1], ["ctl", 20, "제구 20", "obp", 1]]
	for c in cases:
		scene.stats = {"eye": 50, "con": 50, "pw": 50, "vel": 50, "brk": 50, "st": 50, "ctl": 50}
		scene.stats[c[0]] = c[1]
		scene.model.set_stats(scene.stats)
		var r := play(scene, N, 1)
		print("  " + line(c[2], r))
		var diff: float = (r[c[3]] - base[c[3]]) * c[4]
		ok(diff > 0.0, "%s → %s %s (%.3f → %.3f)" % [c[2], c[3], "오름" if c[4] > 0 else "내림", base[c[3]], r[c[3]]])
	scene.stats = {"eye": 50, "con": 50, "pw": 50, "vel": 50, "brk": 50, "st": 50, "ctl": 50}
	scene.model.set_stats(scene.stats)

	print("② 시간 효과 (공 도착 시간)")
	var t50: float = scene.effective_base_ms()
	scene.stats["eye"] = 90; scene.model.set_stats(scene.stats)
	var teye: float = scene.effective_base_ms()
	scene.stats["eye"] = 50; scene.stats["vel"] = 70; scene.model.set_stats(scene.stats)
	var tvel: float = scene.effective_base_ms()
	print("  기본 %.0fms, 선구 90 → %.0fms, 구속 70 → %.0fms" % [t50, teye, tvel])
	ok(teye > t50, "선구가 높으면 공이 느려짐")
	ok(tvel / t50 > 0.93 and tvel / t50 < 0.96, "구속 70이면 약 5%% 빨라짐 (%.3f배, 선구 대결 몫 포함)" % (tvel / t50))
	scene.stats["vel"] = 50; scene.model.set_stats(scene.stats)

	print("③ 조절판 누르기")
	scene.state = scene.State.SHOW
	var tap := func(p: Vector2):
		var e := InputEventScreenTouch.new(); e.pressed = true; e.position = p
		scene._input(e)
	tap.call(scene.PANEL_BTN.get_center())
	ok(scene.panel_open, "조절판 버튼으로 열림")
	tap.call(scene._plus_rect(1).get_center())
	ok(scene.stats["con"] == 60, "정확 +10 → 60")
	tap.call(scene._minus_rect(2).get_center())
	ok(scene.stats["pw"] == 40, "파워 −10 → 40")
	ok(is_equal_approx(scene.model.pl, -10.0), "모델에도 바로 반영 (파워 맞대결 값 −10)")
	var n: int = scene.STAT_ROWS.size()
	tap.call(scene._plus_rect(n).get_center())
	ok(is_equal_approx(scene.base_ms, 700.0), "도착 시간 +50 → 700ms")
	var dr: Rect2 = scene._row_rect(n + 1)
	tap.call(dr.position + Vector2(300 + 2 * 130 + 60, 22))
	ok(scene.difficulty == "어려움" and is_equal_approx(scene.base_ms, 500.0), "난이도 어려움 → 500ms")
	var br: Rect2 = scene._row_rect(n + 2)
	tap.call(br.position + Vector2(100, 22))
	ok(scene.tally["PA"] == 0, "기록 초기화")
	tap.call(br.position + Vector2(br.size.x - 100, 22))
	ok(not scene.panel_open, "닫기")
	scene.state = scene.State.FLIGHT
	tap.call(scene.PANEL_BTN.get_center())
	ok(not scene.panel_open, "공이 날아오는 중에는 안 열림")

	print("결과·조절판 테스트: %d개 중 %d개 통과" % [checks, checks - fails])
	quit(1 if fails > 0 else 0)
