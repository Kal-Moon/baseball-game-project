## 2단계 확인: 타석 화면의 입력 판정 (화면 없이).
## 실행: godot --headless --path prototype/batting --script res://tests/input_test.gd
## ① 판정 함수(스와이프 종류·7단계·궁합) ② 실제 화면 장면에 터치 이벤트를 넣어 끝까지 도는지.
extends SceneTree

const SwingInput := preload("res://core/swing_input.gd")
const PitchTypes := preload("res://core/pitch_types.gd")
const Flight := preload("res://core/pitch_flight.gd")

var fails := 0
var checks := 0


func ok(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("실패: ", msg)


func _init() -> void:
	var si := SwingInput.new()
	var H := 720.0
	# ① 스와이프 종류 (우타자)
	ok(si.classify_swipe(Vector2(5, 3), H) == "레벨", "작은 움직임 = 탭 = 레벨")
	ok(si.classify_swipe(Vector2(10, -120), H) == "어퍼", "위 = 어퍼")
	ok(si.classify_swipe(Vector2(-10, 120), H) == "다운", "아래 = 다운")
	ok(si.classify_swipe(Vector2(-150, 20), H) == "당겨치기", "우타자 왼쪽 = 당겨치기")
	ok(si.classify_swipe(Vector2(150, 20), H) == "밀어치기", "우타자 오른쪽 = 밀어치기")
	ok(si.classify_swipe(Vector2(-150, 20), H, false) == "밀어치기", "좌타자 왼쪽 = 밀어치기")
	# 7단계 (레벨, ms 오차 → 단계)
	var arrive := 1_000_000
	var cases := [[0, 0], [9, 0], [-25, -1], [25, 1], [-60, -2], [60, 2], [-150, -3], [150, 3]]
	for c in cases:
		var lv = si.timing_level(arrive + c[0] * 1000, arrive, "레벨")
		ok(lv == c[1], "레벨 %+dms → %d (나옴 %s)" % [c[0], c[1], str(lv)])
	ok(si.timing_level(arrive + 250_000, arrive, "레벨") == null, "미트 도착 0.2초 뒤 입력은 무시")
	ok(si.timing_level(arrive - 15_000, arrive, "당겨치기") == 0, "당겨치기는 15ms 일찍이 완벽")
	ok(si.timing_level(arrive + 15_000, arrive, "밀어치기") == 0, "밀어치기는 15ms 늦게가 완벽")
	ok(SwingInput.grade(-3) == 0 and SwingInput.grade(1) == 2 and SwingInput.grade(0) == 3, "7단계 → 모델 4단계")
	# 궁합
	ok(si.compat(0.1, 0.1, "레벨") == 0, "가운데 원 + 레벨 = 좋음")
	ok(si.compat(0.0, 0.8, "다운") == 0 and si.compat(0.0, 0.8, "어퍼") == 2, "높은 공: 다운 좋음, 어퍼 나쁨")
	ok(si.compat(0.0, -0.8, "어퍼") == 0 and si.compat(0.0, -0.8, "다운") == 2, "낮은 공: 어퍼 좋음, 다운 나쁨")
	ok(si.compat(-0.8, 0.0, "당겨치기") == 0 and si.compat(-0.8, 0.0, "밀어치기") == 2, "몸쪽: 당겨치기 좋음")
	ok(si.compat(0.8, 0.0, "밀어치기") == 0 and si.compat(0.8, 0.0, "당겨치기") == 2, "바깥쪽: 밀어치기 좋음")
	# 공 비행: 도착 시간과 마지막 위치
	var f := Flight.new()
	f.setup("커브", {"x": 0.3, "y": -0.5}, 650.0, 0)
	ok(absf(f.travel_ms - 650.0 * 145.0 / f.kmh) < 0.01 and f.kmh == 123.0, "커브 123km/h 도착 시간 = 650 × 145/123 (나옴 %.0fms)" % f.travel_ms)
	var fv := Flight.new()
	fv.setup("포심", {"x": 0.0, "y": 0.0}, 650.0, 0, 50.0, 150.0)
	ok(fv.kmh == 175.0 and absf(fv.travel_ms - 650.0 * 145.0 / 175.0) < 0.01, "구속 150 → 175km/h, 도착 %.0fms (표시 구속과 도착 시간이 맞음)" % fv.travel_ms)
	var fg := Flight.new()
	fg.setup("커브", {"x": 0.0, "y": 0.0}, 650.0, 0, 50.0, 50.0, 0.0, 2.0)
	ok(fg.travel_ms > f.travel_ms + 100.0, "구속 차이 과장 2배면 커브가 더 느려짐 (%.0f → %.0fms)" % [f.travel_ms, fg.travel_ms])
	# 화면에서 휘는 폭: 커브는 직선과 확실히 다르게 (변화 크기 2배, 진행 80%·95%)
	var fc := Flight.new()
	fc.setup("커브", {"x": 0.0, "y": -0.3}, 650.0, 0, 50.0, 50.0, 0.0, 1.0, 2.0)
	var to_s := func(z: Vector2) -> Vector2: return Vector2(640, 470) + Vector2(z.x * 85, -z.y * 100)
	for pp in [0.8, 0.95]:
		var q: float = pp / (pp + (1.0 - pp) * 3.0)
		# 타자가 보는 휨 = 처음에 향하던 곳(휘지 않았다면 갔을 곳)으로 가는 직선에서 벗어난 거리
		var straight: Vector2 = Vector2(668, 215).lerp(to_s.call(fc.target - fc.move), q)
		var d := fc.screen_pos(pp, Vector2(668, 215), to_s, q).distance_to(straight)
		ok(d > 25.0, "커브가 진행 %d%%에서 처음 향하던 직선보다 %.0fpx 벗어남 (25px 넘어야 함)" % [roundi(pp * 100), d])
	var ff := Flight.new()
	ff.setup("포심", {"x": 0.0, "y": -0.3}, 650.0, 0, 50.0, 50.0, 0.0, 1.0, 2.0)
	var q8 := 0.8 / (0.8 + 0.2 * 3.0)
	var dff := ff.screen_pos(0.8, Vector2(668, 215), to_s, q8).distance_to(Vector2(668, 215).lerp(to_s.call(ff.target - ff.move), q8))
	var dfc := fc.screen_pos(0.8, Vector2(668, 215), to_s, q8).distance_to(Vector2(668, 215).lerp(to_s.call(fc.target - fc.move), q8))
	ok(dfc > dff * 3.0, "커브 휘는 폭(%.0fpx)이 포심(%.0fpx)의 3배 넘음" % [dfc, dff])
	ok(f.zone_pos(1.0).distance_to(Vector2(0.3, -0.5)) < 1e-6, "공은 정한 위치에 도착")
	ok(f.zone_pos(0.0).y > -0.5, "커브는 처음엔 더 높게 보였다가 떨어짐")
	var f2 := Flight.new()
	f2.setup("싱커", {"x": 0.0, "y": 0.0}, 650.0, 0)
	ok(f2.zone_pos(0.0).x > 0.0, "오른손 싱커는 우타자 몸쪽(x<0)으로 휨 → 처음엔 바깥쪽에서 출발")
	for n in PitchTypes.NAMES:
		ok(PitchTypes.LIST.has(n), "구종 %s" % n)
	ok(PitchTypes.NAMES.size() == 11, "기본 구종 11개")

	# ② 장면에 이벤트 넣기
	var scene: Node2D = load("res://ui/at_bat.tscn").instantiate()
	root.add_child(scene)
	scene.fake_now = 0
	scene._ready()
	scene.throw_pitch("포심", {"x": 0.0, "y": 0.0, "kind": "normal"})
	var arr: int = scene.flight.arrive_usec
	scene.fake_now = arr - 20_000
	var down := InputEventScreenTouch.new(); down.pressed = true; down.position = Vector2(640, 500)
	scene._input(down)
	var drag := InputEventScreenDrag.new(); drag.position = Vector2(640, 380)
	scene._input(drag)
	ok(scene.swing == "어퍼", "끌어올리는 중에 어퍼로 정해짐 (나옴 %s)" % scene.swing)
	ok(scene.level == -1, "20ms 일찍 = 좋음(빠른 쪽) (나옴 %s)" % str(scene.level))
	ok(scene.bat_start >= 0 and scene.bat_swing == "어퍼", "배트가 어퍼로 휘둘러짐")
	ok(scene.contact in ["", "foul", "weak", "normal", "strong"], "맞았는지 판정 (나옴 %s)" % scene.contact)
	# 반응 통계: 완벽 타이밍 + 가운데 공은 대부분 맞아야 함
	var hits := 0
	for i in 200:
		scene.throw_pitch("포심", {"x": 0.0, "y": 0.0, "kind": "normal"})
		scene.fake_now = scene.flight.arrive_usec
		scene._input(down)
		var up0 := InputEventScreenTouch.new(); up0.pressed = false; up0.position = Vector2(640, 500)
		scene._input(up0)
		if scene.contact != "": hits += 1
	ok(hits >= 170, "완벽 타이밍 200번 중 맞음 %d번 (170번 이상)" % hits)
	scene.throw_pitch("포심", {"x": 0.0, "y": 0.0, "kind": "normal"})
	arr = scene.flight.arrive_usec
	scene.fake_now = arr - 20_000
	scene._input(down)
	scene._input(drag)
	scene.fake_now = arr + 300_000
	scene.tick()
	ok(scene.state == scene.State.SHOW, "투구 뒤 표시 단계로 넘어감")
	ok(scene.last_text.begins_with("좋음 ◀ · 포심 145km/h"), "투구 뒤 글자 (나옴 %s)" % scene.last_text)
	# 스윙 안 함
	scene.throw_pitch("슬라이더", {"x": 1.4, "y": 0.0, "kind": "normal"})
	scene.fake_now = scene.flight.arrive_usec + 300_000
	scene.tick()
	ok(scene.last_sub == "볼", "스윙 안 한 존 밖 공 = 볼")
	# 공이 손을 떠나기 전 터치는 무시
	scene._enter(scene.State.WINDUP, 600)
	scene._input(down)
	ok(scene.touch_usec == -1 or scene.state != scene.State.FLIGHT, "와인드업 중 터치 무시")

	print("입력 테스트: %d개 중 %d개 통과" % [checks, checks - fails])
	quit(1 if fails > 0 else 0)
