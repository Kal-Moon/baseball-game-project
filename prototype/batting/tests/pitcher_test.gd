## 3단계 확인: AI 투수 (화면 없이). docs/game-design.md 4.1절 표 3단계 "투구 1,000개 자동 기록".
## 실행: godot --headless --path prototype/batting --script res://tests/pitcher_test.gd -- [CSV 저장 경로]
## ① 투수 2만 명을 만들어 구종 수·구종 확률을 문서 값과 비교
## ② 실제 화면 장면으로 투구 1,000개를 자동으로 던지고 치게 해서(보통 유저 흉내) 기록·볼배합 확인
## ③ 구종 고정 옵션
extends SceneTree

const AiPitcher := preload("res://core/ai_pitcher.gd")
const Params := preload("res://core/params.gd")
const Model := preload("res://core/batting_model.gd")

var fails := 0
var checks := 0


func ok(cond: bool, msg: String) -> void:
	checks += 1
	print(("  통과  " if cond else "  실패  ") + msg)
	if not cond: fails += 1


func _init() -> void:
	var rng := RandomNumberGenerator.new(); rng.seed = 7
	var ap := AiPitcher.new(rng)
	# ① 투수 만들기
	var N := 20000
	var n_count := {}; var has := {}; var fb_ok := true; var grade_n := {}
	for i in N:
		ap.new_pitcher()
		n_count[ap.pitches.size()] = n_count.get(ap.pitches.size(), 0) + 1
		if not (ap.pitches[0] in AiPitcher.FASTBALLS): fb_ok = false
		for p in ap.pitches:
			has[p] = has.get(p, 0) + 1
			grade_n[ap.grades[p]] = grade_n.get(ap.grades[p], 0) + 1
	print("① 투수 %d명" % N)
	var cs := ""
	for k in [2, 3, 4, 5, 6]:
		var pct: float = 100.0 * n_count.get(k, 0) / N
		cs += "%d개 %.1f%%  " % [k, pct]
		ok(absf(pct - AiPitcher.COUNT_W[k]) < 1.5, "구종 %d개 비율 %.1f%% (문서 %.0f%%)" % [k, pct, AiPitcher.COUNT_W[k]])
	ok(fb_ok, "모든 투수가 패스트볼 계열 1개 이상")
	print("  구종별 가진 투수 비율 (나옴 / 문서 2.3절 한국 리그):")
	var doc := AiPitcher.PROB.duplicate(); doc["체인지업"] = 42.0 * (1 - AiPitcher.CIRCLE_SHARE); doc["서클체인지업"] = 42.0 * AiPitcher.CIRCLE_SHARE
	var keys := ["포심", "싱커", "커터", "슬라이더", "스위퍼", "커브", "너클커브", "체인지업", "서클체인지업", "스플리터", "포크볼"]
	var rows := []
	for p in keys:
		var pct: float = 100.0 * has.get(p, 0) / N
		rows.append("%s %.0f/%.0f" % [p, pct, doc[p]])
	print("    " + ", ".join(rows))
	for p in ["포심", "싱커", "커터", "슬라이더", "커브"]:
		var pct2: float = 100.0 * has.get(p, 0) / N
		ok(pct2 >= doc[p] - 2.0 and pct2 <= doc[p] * 1.15, "%s 가진 투수 %.0f%% (문서 %.0f%%, 구종 수 비율 때문에 최대 약 +10%%)" % [p, pct2, doc[p]])
	var g := ""
	var gt := 0
	for k in grade_n: gt += grade_n[k]
	for k in ["S", "A", "B", "C", "D"]: g += "%s %.0f%%  " % [k, 100.0 * grade_n.get(k, 0) / gt]
	print("  구종 등급 분포: " + g)

	# ② 장면으로 1,000구
	var scene: Node2D = load("res://ui/at_bat.tscn").instantiate()
	root.add_child(scene)
	scene.fake_now = 0
	scene._ready()
	var user: Dictionary = Params.USERS["보통"]
	var urng := RandomNumberGenerator.new(); urng.seed = 11
	var pitches := 0
	while pitches < 1000:
		scene.next_pitch()
		var f = scene.flight
		var zone := Model.in_zone(f.target.x, f.target.y)
		var p_sw: float = user["zone_swing"] if zone else user["chase"]
		if scene.strikes == 2: p_sw = minf(0.95, p_sw + (0.15 if zone else 0.05))
		if urng.randf() < p_sw:
			# 보통 유저 흉내: 터치 오차 표준편차 60ms (2단계 구간 폭을 잡은 가정과 같음), 스윙 종류는 랜덤
			var err := urng.randfn(0.0, 60.0)
			scene.fake_now = f.arrive_usec + int(err * 1000.0)
			var d := InputEventScreenTouch.new(); d.pressed = true; d.position = Vector2(640, 500)
			scene._input(d)
			var dirs := [Vector2.ZERO, Vector2(0, -120), Vector2(0, 120), Vector2(-150, 0), Vector2(150, 0)]
			var u := InputEventScreenTouch.new(); u.pressed = false; u.position = Vector2(640, 500) + dirs[urng.randi_range(0, 4)]
			scene._input(u)
		scene.fake_now = f.arrive_usec + 300_000
		scene.tick()
		pitches += 1
	var log: Array = scene.pitch_log
	print("② 투구 %d개, 타석 %d개" % [log.size(), scene.pa_no])
	ok(log.size() == 1000, "투구 1,000개 기록")
	# 볼카운트별 패스트볼 비율
	var by := {}
	for r in log:
		var c: String = r["count"]
		if not by.has(c): by[c] = [0, 0]
		by[c][0] += 1
		if r["pitch"] in AiPitcher.FASTBALLS: by[c][1] += 1
	var line := ""
	for c in ["0-0", "0-1", "0-2", "1-0", "1-1", "1-2", "2-0", "2-1", "2-2", "3-0", "3-1", "3-2"]:
		if by.has(c): line += "%s %d%%(%d구) " % [c, roundi(100.0 * by[c][1] / by[c][0]), by[c][0]]
	print("  볼카운트별 패스트볼 계열 비율 (MLB 2025: 0-0 60%, 0-2 42%, 3-0 94%):\n    " + line)
	var fb_all := 0; var zone_n := 0
	for r in log:
		if r["pitch"] in AiPitcher.FASTBALLS: fb_all += 1
		if r["zone"]: zone_n += 1
	print("  전체 패스트볼 계열 %.1f%% (MLB 2025 약 55%%, 투구 구성이 투수마다 달라 조금 다를 수 있음), 존 안 %.1f%%" % [100.0 * fb_all / log.size(), 100.0 * zone_n / log.size()])
	ok(absf(100.0 * fb_all / log.size() - 55.0) < 8.0, "전체 패스트볼 계열 비율이 55% ±8 안")
	ok(by.get("0-2", [1, 0])[1] * 1.0 / by.get("0-2", [1, 1])[0] < by.get("0-0", [1, 1])[1] * 1.0 / by.get("0-0", [1, 1])[0], "0-2에서 0-0보다 변화구를 더 던짐")
	var ends := {}
	for r in log:
		if r["end"] != "": ends[r["end"]] = ends.get(r["end"], 0) + 1
	print("  타석 끝: ", ends)
	for r in log:
		if not (r["pitch"] in r["pitcher"].split("/")):
			ok(false, "던진 구종이 그 투수의 구종 목록에 있음 (%s / %s)" % [r["pitch"], r["pitcher"]])
			break
	ok(true, "던진 구종은 모두 그 투수의 구종")
	# CSV
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		var fa := FileAccess.open(args[0], FileAccess.WRITE)
		fa.store_line("pa,pitcher,count,pitch,grade,x,y,zone,kind,swing,level,result,call,end")
		for r in log:
			fa.store_line("%d,%s,%s,%s,%s,%.3f,%.3f,%s,%s,%s,%s,%s,%s,%s" % [r["pa"], r["pitcher"], r["count"], r["pitch"], r["grade"],
				r["x"], r["y"], r["zone"], r["kind"], r["swing"], str(r["level"]), r["result"], r["call"], r["end"]])
		fa.close()
		print("  CSV 저장: ", args[0])
	# ③ 구종 고정
	scene.pitcher.locked = "커브"
	var all_curve := true
	for i in 30:
		scene.next_pitch()
		if scene.flight.name != "커브": all_curve = false
		scene.fake_now = scene.flight.arrive_usec + 300_000
		scene.tick()
	ok(all_curve, "구종 고정 = 커브면 30구 모두 커브")
	var tap := InputEventScreenTouch.new(); tap.pressed = true; tap.position = scene.LOCK_RECT.get_center()
	scene._input(tap)
	ok(scene.pitcher.locked == "너클커브", "버튼을 누르면 다음 구종으로 (커브 → 너클커브, 나옴 %s)" % scene.pitcher.locked)

	print("AI 투수 테스트: %d개 중 %d개 통과" % [checks, checks - fails])
	quit(1 if fails > 0 else 0)
