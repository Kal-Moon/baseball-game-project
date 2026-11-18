## 타석 화면 (도형). docs/game-design.md 4.1절 표 2·3단계.
## 2단계: 존 테두리, 날아오는 공(원근 + 회전 그림), 스와이프 입력(터치 시각 기준), 투구 뒤 표시.
## 3단계: 타석마다 랜덤 AI 투수, 볼배합(볼카운트별), 볼카운트·삼진·볼넷·사구, 구종 고정 버튼.
## 4단계: 인플레이 결과(안타·아웃 글자 + 작은 경기장 궤적), 타석 기록 합계, 조절판(능력치·공 도착 시간·난이도).
extends Node2D

const Model := preload("res://core/batting_model.gd")
const PitchTypes := preload("res://core/pitch_types.gd")
const Flight := preload("res://core/pitch_flight.gd")
const SwingInput := preload("res://core/swing_input.gd")
const AiPitcher := preload("res://core/ai_pitcher.gd")
const Batted := preload("res://core/batted_ball.gd")

## 화면 배치 (1280×720 기준)
const ZONE_C := Vector2(640, 470)
const ZONE_H := Vector2(85, 100)        # 존 반폭·반높이 (px)
const RELEASE := Vector2(668, 215)      # 투수 손 위치
const PERSP := 3.0                      # 원근 정도 (클수록 마지막에 확 커짐)

enum State { WAIT, WINDUP, FLIGHT, SHOW }

var model := Model.new(int(Time.get_ticks_usec()))
var input := SwingInput.new()
var flight := Flight.new()
var state := State.WAIT
var state_until := 0                    # usec
var base_ms := 650.0                    # 포심(구속 50) 도착 시간 (조절판, 시작 650ms, 4.1절)
var difficulty := "보통"
const DIFF_MS := {"쉬움": 800.0, "보통": 650.0, "어려움": 500.0}   # 4.1절 "난이도"
## 능력치 (조절판). 타자: eye 선구 · con 정확 · pw 파워 / 투수: vel 구속 · brk 변화 · st 구위 · ctl 제구
var stats := {"eye": 50, "con": 50, "pw": 50, "vel": 50, "brk": 50, "st": 50, "ctl": 50}
const STAT_ROWS := [["eye", "타자 선구"], ["con", "타자 정확"], ["pw", "타자 파워"],
	["vel", "투수 구속"], ["brk", "투수 변화"], ["st", "투수 구위"], ["ctl", "투수 제구"]]
## 타석 기록 합계 (조절판에서 초기화)
var tally := {"PA": 0, "AB": 0, "H": 0, "2B": 0, "3B": 0, "HR": 0, "K": 0, "BB": 0, "HBP": 0}
var hit_info := {}                      # 이번 인플레이 타구 (글자·궤적)
var show_start := 0
## 조절판
const PANEL_BTN := Rect2(1040, 98, 224, 46)
const PANEL := Rect2(220, 70, 840, 590)
var panel_open := false
var right_batter := true
var pitcher: AiPitcher
var balls := 0
var strikes := 0
var pa_no := 1
var pa_over := false                    # 이번 공으로 타석이 끝났으면 다음 공 전에 새 투수
var swing_result := ""                  # 1단계 모델 결과 (whiff / foul / weak / normal / strong)
var pitch_log: Array = []               # 공마다 기록 (5단계에서 CSV로 저장)
var pitch_count := "0-0"                # 이 공을 던질 때 볼카운트
## 구종 고정 버튼 (4.1절 "조절판에서 구종 하나만 던지게 고정". 조절판 전체는 4단계)
const LOCK_RECT := Rect2(1040, 44, 224, 46)

# 이번 투구의 스윙
var touch_usec := -1
var touch_pos := Vector2.ZERO
var swing := ""                         # 비어 있으면 아직 스윙 종류 미정
var level = null                        # 7단계, null = 스윙 안 함/무시
var last_text := ""
var last_sub := ""
# 스윙 반응 (확인용 최소 연출: 배트 도형 + 맞으면 번쩍임·진동)
const BAT_MS := 180.0                   # 배트 휘두르는 시간
var bat_start := -1                     # usec, -1 = 안 휘두름
var bat_swing := ""
var contact := ""                       # "" 헛스윙/없음, foul / weak / normal / strong
var flash_start := -1

## 테스트용: 시각을 밖에서 넣을 수 있게 (null이면 실제 시각)
var fake_now = null


func now() -> int:
	return fake_now if fake_now != null else Time.get_ticks_usec()


func _ready() -> void:
	model.set_stats(stats)
	pitcher = AiPitcher.new(model.rng)
	pitcher.new_pitcher()
	_enter(State.WAIT, 800)


func _enter(s: State, ms: int) -> void:
	state = s
	state_until = now() + ms * 1000


func _process(_dt: float) -> void:
	tick()
	queue_redraw()


func tick() -> void:
	if panel_open:
		return                               # 조절판이 열려 있는 동안 멈춤 (투구 사이에만 열 수 있음)
	var t := now()
	match state:
		State.WAIT:
			if t >= state_until:
				_enter(State.WINDUP, 600)
		State.WINDUP:
			if t >= state_until:
				next_pitch()
		State.FLIGHT:
			if t >= flight.arrive_usec + int(input.late_cutoff * 1000.0):
				_finish_pitch()
		State.SHOW:
			if t >= state_until:
				_enter(State.WAIT, 300)


## AI 투수가 다음 공을 던짐: 타석이 끝났으면 새 투수, 볼배합으로 구종, 등급 원 배율로 위치
func next_pitch() -> void:
	if pa_over:
		start_new_pa()
	var p: String = pitcher.choose_pitch(balls, strikes)
	pitch_count = "%d-%d" % [balls, strikes]
	throw_pitch(p, model.pitch_location(balls, strikes, pitcher.circle_mult(p)))


func start_new_pa() -> void:
	pa_over = false
	balls = 0
	strikes = 0
	pa_no += 1
	pitcher.new_pitcher()


## 실제 도착 시간에 능력치를 넣음 (4.1절 표): 선구 × (1 + 느려짐), 구속 +20 → −5%
func effective_base_ms() -> float:
	var v := clampf(float(stats["vel"]) - 50.0, -40.0, 20.0)
	return base_ms * (1.0 + model.slow) * (1.0 - 0.05 * v / 20.0)


func throw_pitch(p_name: String, loc: Dictionary) -> void:
	flight.setup(p_name, loc, effective_base_ms(), now(), float(stats["brk"]), float(stats["vel"]))
	touch_usec = -1
	swing = ""
	level = null
	bat_start = -1
	contact = ""
	swing_result = ""
	flash_start = -1
	state = State.FLIGHT


## ---- 입력: 손가락이 닿은 시각이 타이밍, 이어지는 움직임이 스윙 종류 ----

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed and panel_open:
			panel_tap(event.position)
			return
		if event.pressed and PANEL_BTN.has_point(event.position):
			if state != State.FLIGHT:        # 공이 날아오는 중에는 안 열림
				panel_open = true
			return
		if event.pressed and LOCK_RECT.has_point(event.position):
			_cycle_lock()                    # 버튼 누름은 스윙으로 치지 않음
			return
		if event.pressed:
			on_touch_down(event.position, now())
		else:
			on_touch_up(event.position)
	elif event is InputEventScreenDrag:
		on_drag(event.position)


func _cycle_lock() -> void:
	var opts: Array = [""] + PitchTypes.NAMES
	pitcher.locked = opts[(opts.find(pitcher.locked) + 1) % opts.size()]


func on_touch_down(pos: Vector2, t_usec: int) -> void:
	if state != State.FLIGHT or touch_usec >= 0:
		return                               # 투구 중 첫 터치만 스윙 (공이 손을 떠나기 전 터치는 무시)
	if t_usec > flight.arrive_usec + int(input.late_cutoff * 1000.0):
		return
	touch_usec = t_usec
	touch_pos = pos
	bat_start = t_usec                     # 배트는 손가락이 닿자마자 출발 (종류는 곧 정해짐)
	bat_swing = "레벨"


func on_drag(pos: Vector2) -> void:
	# 충분히 움직였으면 바로 스윙 종류를 정함 (손을 떼기 전에)
	if touch_usec >= 0 and swing == "" and (pos - touch_pos).length() >= 2.0 * input.swipe_min * _screen_h():
		_decide_swing(pos)


func on_touch_up(pos: Vector2) -> void:
	if touch_usec >= 0 and swing == "":
		_decide_swing(pos)


func _decide_swing(pos: Vector2) -> void:
	swing = input.classify_swipe(pos - touch_pos, _screen_h(), right_batter)
	level = input.timing_level(touch_usec, flight.arrive_usec, swing)
	bat_swing = swing
	_judge_contact()


## 맞았는지만 정해 반응을 보여 줌 (결과 글자·안타 판정은 4단계). 1단계 계산 모델 그대로.
func _judge_contact() -> void:
	contact = ""
	if level == null:
		return
	var zone := Model.in_zone(flight.target.x, flight.target.y)
	var c := input.compat(flight.target.x, flight.target.y, swing)
	var res: String = model.resolve_swing(SwingInput.grade(level), zone, flight.kind, c, false)[0]
	swing_result = res
	if res != "whiff":
		contact = res
		flash_start = maxi(now(), flight.arrive_usec)   # 번쩍임은 공이 배트에 닿는 순간에
		Input.vibrate_handheld(60 if res == "strong" else 30)


func _screen_h() -> float:
	return 720.0


func _finish_pitch() -> void:
	if touch_usec >= 0 and swing == "":
		swing = "레벨"                       # 손을 안 뗀 채 끝나면 탭으로
		level = input.timing_level(touch_usec, flight.arrive_usec, swing)
		bat_swing = swing
		_judge_contact()
	var pitch_info := "%s %dkm/h" % [flight.name, flight.kmh]
	var zone := Model.in_zone(flight.target.x, flight.target.y)
	var call := ""                          # 이 공의 판정
	if level == null:
		last_text = pitch_info
		if model.is_hbp(flight.target.x):
			call = "사구"
		elif zone:
			call = "스트라이크"; strikes += 1
		else:
			call = "볼"; balls += 1
	else:
		last_text = "%s · %s" % [SwingInput.TIMING_NAMES[level], pitch_info]
		match swing_result:
			"whiff": call = "헛스윙"; strikes += 1
			"foul": call = "파울"; strikes = mini(2, strikes + 1)
			_: call = "인플레이"
	var end := ""
	hit_info = {}
	if call == "사구":
		end = "몸에 맞는 공"; tally["HBP"] += 1
	elif call == "인플레이":
		var outcome := model.ball_in_play(swing_result)
		var a := Batted.angle(swing, level, model.rng, right_batter)
		hit_info = Batted.describe(outcome, swing_result, swing, a, model.rng)
		end = hit_info["text"]
		tally["AB"] += 1
		if outcome != "OUT": tally["H"] += 1
		if outcome in ["2B", "3B", "HR"]: tally[outcome] += 1
	elif balls >= 4:
		end = "볼넷"; tally["BB"] += 1
	elif strikes >= 3:
		end = "삼진"; tally["K"] += 1; tally["AB"] += 1
	if end != "": tally["PA"] += 1
	last_sub = call
	if level != null:
		last_sub += "  ·  %s (%+d ms)" % [swing, roundi(float(touch_usec - flight.arrive_usec) / 1000.0)]
		last_sub += ["  궁합 좋음", "", "  반대 스윙"][input.compat(flight.target.x, flight.target.y, swing)]   # 시험판 확인용, 실제 게임은 표시 안 함 (3.1절)
	if end != "":
		last_sub += "   →  " + end
		pa_over = true
	pitch_log.append({"pa": pa_no, "pitcher": "/".join(pitcher.pitches), "pitch": flight.name,
		"grade": pitcher.grades.get(flight.name, "-"), "count": pitch_count,
		"x": flight.target.x, "y": flight.target.y, "zone": zone, "kind": flight.kind,
		"swing": swing, "level": level, "result": swing_result, "call": call, "end": end})
	show_start = now()
	_enter(State.SHOW, 2200 if not hit_info.is_empty() else 1500)


## ---- 그리기 ----

static func zone_to_screen(z: Vector2) -> Vector2:
	return ZONE_C + Vector2(z.x * ZONE_H.x, -z.y * ZONE_H.y)


static func persp(p: float) -> float:
	return p / (p + (1.0 - p) * PERSP)


func _draw() -> void:
	# 배경: 외야 쪽 하늘·잔디, 마운드
	draw_rect(Rect2(0, 0, 1280, 300), Color("#20344f"))
	draw_rect(Rect2(0, 300, 1280, 420), Color("#2f6b3a"))
	draw_circle(Vector2(668, 250), 46, Color("#8a6a45"))
	# 투수 (도형)
	var arm := 0.0
	if state == State.WINDUP:
		arm = 1.0 - float(state_until - now()) / 600000.0
	draw_rect(Rect2(656, 175, 24, 60), Color("#d9d9d9"))
	draw_circle(Vector2(668, 166), 10, Color("#d9d9d9"))
	draw_line(Vector2(676, 185), Vector2(676, 185) + Vector2(14, -18).rotated(arm * 2.5), Color("#d9d9d9"), 5)
	# 홈플레이트
	draw_colored_polygon(PackedVector2Array([Vector2(600, 640), Vector2(680, 640), Vector2(680, 660), Vector2(640, 685), Vector2(600, 660)]), Color("#eeeeee"))
	# 우타자 뒷모습 (반투명, 왼쪽)
	var bx := 430.0 if right_batter else 850.0
	draw_rect(Rect2(bx - 55, 380, 110, 340), Color(0.1, 0.1, 0.15, 0.55))
	draw_circle(Vector2(bx, 350), 42, Color(0.1, 0.1, 0.15, 0.55))
	# 스트라이크 존 테두리 (3.1절: 테두리만)
	var tl := zone_to_screen(Vector2(-1, 1))
	draw_rect(Rect2(tl, ZONE_H * 2.0), Color(1, 1, 1, 0.8), false, 2.0)

	if state == State.FLIGHT:
		var p := flight.progress(now())
		if p < 1.0 and not (contact != "" and now() >= flash_start):
			_draw_ball(p)
	_draw_bat()
	_draw_flash()
	if state == State.SHOW:
		# 공이 지나간 자리 (3.1절)
		draw_circle(zone_to_screen(flight.target), 9, Color(1, 0.85, 0.2, 0.9))
		draw_arc(zone_to_screen(flight.target), 9, 0, TAU, 24, Color.BLACK, 1.5)
		var font := ThemeDB.fallback_font
		draw_string(font, Vector2(0, 85), last_text, HORIZONTAL_ALIGNMENT_CENTER, 1280, 40, Color.WHITE)
		draw_string(font, Vector2(0, 122), last_sub, HORIZONTAL_ALIGNMENT_CENTER, 1280, 24, Color(1, 1, 1, 0.8))
		if not hit_info.is_empty():
			_draw_field(font)
	var info := ThemeDB.fallback_font
	draw_string(info, Vector2(16, 30), "타격 시험판 · 탭=레벨  위=어퍼  아래=다운  ←=당겨치기  →=밀어치기 (우타자)", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(1, 1, 1, 0.7))
	_draw_count(info)
	# 상대 투수 구종 목록 (타석 화면 구석, 2.3절 "쓰임 후보")
	draw_string(info, Vector2(16, 690), "%d번째 타석 · 상대 투수: %s" % [pa_no, " · ".join(pitcher.pitches)], HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(1, 1, 1, 0.85))
	# 구종 고정 버튼
	draw_rect(LOCK_RECT, Color(0, 0, 0, 0.45))
	draw_rect(LOCK_RECT, Color(1, 1, 1, 0.6), false, 1.5)
	var lock_txt := "구종 고정: " + (pitcher.locked if pitcher.locked != "" else "없음")
	draw_string(info, LOCK_RECT.position + Vector2(0, 31), lock_txt, HORIZONTAL_ALIGNMENT_CENTER, LOCK_RECT.size.x, 20, Color.WHITE)
	# 조절판 버튼과 기록 합계
	draw_rect(PANEL_BTN, Color(0, 0, 0, 0.45))
	draw_rect(PANEL_BTN, Color(1, 1, 1, 0.6), false, 1.5)
	draw_string(info, PANEL_BTN.position + Vector2(0, 31), "조절판", HORIZONTAL_ALIGNMENT_CENTER, PANEL_BTN.size.x, 20, Color.WHITE)
	draw_string(info, Vector2(700, 690), tally_text(), HORIZONTAL_ALIGNMENT_RIGHT, 564, 19, Color(1, 1, 1, 0.85))
	if panel_open:
		_draw_panel(info)


func tally_text() -> String:
	var avg: float = float(tally["H"]) / tally["AB"] if tally["AB"] > 0 else 0.0
	return "%d타석  타율 %s  안타 %d  홈런 %d  삼진 %d  볼넷 %d" % [tally["PA"], ("%.3f" % avg).trim_prefix("0"), tally["H"], tally["HR"], tally["K"], tally["BB"]]


## 작은 경기장에 타구 궤적 (위에서 본 부채꼴, 0.8초 동안 날아감)
func _draw_field(font: Font) -> void:
	var home := Vector2(1150, 330)
	var R := 120.0
	var pts := PackedVector2Array([home])
	for i in 17:
		pts.append(home + Vector2(0, -R).rotated(deg_to_rad(-45.0 + 90.0 * i / 16.0)))
	draw_colored_polygon(pts, Color(0.15, 0.45, 0.2, 0.9))
	draw_polyline(pts + PackedVector2Array([home]), Color(1, 1, 1, 0.7), 1.5)
	var infield := PackedVector2Array([home, home + Vector2(32, -32), home + Vector2(0, -64), home + Vector2(-32, -32), home])
	draw_polyline(infield, Color(1, 1, 1, 0.5), 1.0)
	var t := clampf(float(now() - show_start) / 800000.0, 0.0, 1.0)
	var end := home + Vector2(0, -R * float(hit_info["dist"])).rotated(deg_to_rad(float(hit_info["angle"])))
	var cur := home.lerp(end, t)
	if hit_info["fly"]:
		cur += Vector2(0, -28.0 * sin(PI * t) * float(hit_info["dist"]))   # 뜬공은 위로 솟았다가 떨어지게
	draw_line(home, home.lerp(end, t), Color(1, 1, 1, 0.35), 2.0)
	draw_circle(cur, 5.0, Color("#ffe066") if hit_info["hit"] else Color.WHITE)


## ---- 조절판 (4.1절: 능력치 값을 바꿔 결과 확인, 공 도착 시간, 난이도) ----

func _row_rect(i: int) -> Rect2:
	return Rect2(PANEL.position + Vector2(30, 70 + i * 50), Vector2(PANEL.size.x - 60, 44))


func _minus_rect(i: int) -> Rect2:
	var r := _row_rect(i); return Rect2(r.position + Vector2(380, 0), Vector2(70, 44))


func _plus_rect(i: int) -> Rect2:
	var r := _row_rect(i); return Rect2(r.position + Vector2(580, 0), Vector2(70, 44))


## 행: 0~6 능력치, 7 공 도착 시간, 8 난이도, 9 기록 초기화 / 닫기
func panel_tap(pos: Vector2) -> void:
	for i in STAT_ROWS.size():
		var key: String = STAT_ROWS[i][0]
		if _minus_rect(i).has_point(pos): stats[key] = maxi(0, stats[key] - 10)
		elif _plus_rect(i).has_point(pos): stats[key] = mini(150, stats[key] + 10)   # 100 초과 가능 (성장 전제)
	var n := STAT_ROWS.size()
	if _minus_rect(n).has_point(pos): base_ms = maxf(400.0, base_ms - 50.0)
	elif _plus_rect(n).has_point(pos): base_ms = minf(1000.0, base_ms + 50.0)
	var dr := _row_rect(n + 1)
	var names := ["쉬움", "보통", "어려움"]
	for k in 3:
		if Rect2(dr.position + Vector2(300 + k * 130, 0), Vector2(120, 44)).has_point(pos):
			difficulty = names[k]; base_ms = DIFF_MS[difficulty]
	var br := _row_rect(n + 2)
	if Rect2(br.position, Vector2(300, 44)).has_point(pos):
		for k in tally: tally[k] = 0
	elif Rect2(br.position + Vector2(br.size.x - 200, 0), Vector2(200, 44)).has_point(pos):
		panel_open = false
		_enter(State.WAIT, 800)
	model.set_stats(stats)


func _btn(r: Rect2, txt: String, font: Font, on: bool = false) -> void:
	draw_rect(r, Color(0.25, 0.45, 0.8, 0.9) if on else Color(1, 1, 1, 0.12))
	draw_rect(r, Color(1, 1, 1, 0.6), false, 1.5)
	draw_string(font, r.position + Vector2(0, 30), txt, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 22, Color.WHITE)


func _draw_panel(font: Font) -> void:
	draw_rect(PANEL, Color(0.05, 0.07, 0.12, 0.94))
	draw_rect(PANEL, Color(1, 1, 1, 0.6), false, 2.0)
	draw_string(font, PANEL.position + Vector2(0, 45), "조절판 (값을 바꾸면 다음 공부터 적용)", HORIZONTAL_ALIGNMENT_CENTER, PANEL.size.x, 26, Color.WHITE)
	for i in STAT_ROWS.size():
		var r := _row_rect(i)
		draw_string(font, r.position + Vector2(10, 30), STAT_ROWS[i][1], HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
		_btn(_minus_rect(i), "−10", font)
		draw_string(font, r.position + Vector2(450, 30), str(stats[STAT_ROWS[i][0]]), HORIZONTAL_ALIGNMENT_CENTER, 130, 24, Color("#ffe066"))
		_btn(_plus_rect(i), "+10", font)
	var n := STAT_ROWS.size()
	var tr := _row_rect(n)
	draw_string(font, tr.position + Vector2(10, 30), "포심 도착 시간 (구속 50)", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
	_btn(_minus_rect(n), "−50", font)
	draw_string(font, tr.position + Vector2(450, 30), "%dms" % roundi(base_ms), HORIZONTAL_ALIGNMENT_CENTER, 130, 24, Color("#ffe066"))
	_btn(_plus_rect(n), "+50", font)
	var dr := _row_rect(n + 1)
	draw_string(font, dr.position + Vector2(10, 30), "난이도", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
	var names := ["쉬움", "보통", "어려움"]
	for k in 3:
		_btn(Rect2(dr.position + Vector2(300 + k * 130, 0), Vector2(120, 44)), names[k], font, difficulty == names[k])
	var br := _row_rect(n + 2)
	_btn(Rect2(br.position, Vector2(300, 44)), "기록 초기화", font)
	_btn(Rect2(br.position + Vector2(br.size.x - 200, 0), Vector2(200, 44)), "닫기", font)


## 볼카운트: 볼 초록 4칸, 스트라이크 노랑 3칸 (TV 중계처럼)
func _draw_count(font: Font) -> void:
	var o := Vector2(24, 70)
	draw_rect(Rect2(o - Vector2(10, 22), Vector2(150, 70)), Color(0, 0, 0, 0.45))
	draw_string(font, o + Vector2(0, 2), "B", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
	draw_string(font, o + Vector2(0, 36), "S", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
	for i in 3:
		draw_circle(o + Vector2(36 + i * 28, -6), 9, Color("#3cc35a") if i < balls else Color(1, 1, 1, 0.2))
	for i in 2:
		draw_circle(o + Vector2(36 + i * 28, 28), 9, Color("#f2c335") if i < strikes else Color(1, 1, 1, 0.2))


## 배트: 타자 손에서 나와 존을 가로지르는 막대. 스윙 종류마다 높이 변화가 다름.
## 어퍼 = 아래에서 위로, 다운 = 위에서 아래로, 당겨치기 = 빨리 돌아 왼쪽에서 끝남, 밀어치기 = 늦게 끝까지.
func _draw_bat() -> void:
	if bat_start < 0:
		return
	var t := float(now() - bat_start) / (BAT_MS * 1000.0)
	if t < 0.0 or t > 1.6:
		return
	t = minf(t, 1.0)
	var hands := Vector2(505, clampf(zone_to_screen(flight.target).y, 380.0, 580.0))   # 배트는 공 높이로 (방향형, 커서 없음)
	var dy := {"레벨": [0.0, 0.0], "어퍼": [70.0, -70.0], "다운": [-70.0, 70.0], "당겨치기": [0.0, 0.0], "밀어치기": [0.0, 0.0]}
	var reach := {"레벨": 300.0, "어퍼": 300.0, "다운": 300.0, "당겨치기": 230.0, "밀어치기": 360.0}
	var e := 1.0 - pow(1.0 - t, 2.0)                 # 빨라졌다가 끝에서 느려짐
	var d: Array = dy[bat_swing]
	var tip := hands + Vector2(lerpf(-110.0, float(reach[bat_swing]), e), lerpf(d[0], d[1], e))
	var hand_now := hands + Vector2(lerpf(-20.0, 30.0, e), lerpf(d[0], d[1], e) * 0.3)
	draw_line(hand_now, tip, Color("#c89b5a"), 9.0)
	draw_circle(tip, 5.5, Color("#c89b5a"))


## 맞았을 때 번쩍임 (강한 타구일수록 크게)
func _draw_flash() -> void:
	if contact == "" or flash_start < 0:
		return
	var t := float(now() - flash_start) / 250000.0
	if t < 0.0 or t > 1.0:
		return
	var size: float = {"foul": 30.0, "weak": 35.0, "normal": 50.0, "strong": 75.0}[contact]
	var c := Color(1, 1, 0.75, 1.0 - t)
	var pos := zone_to_screen(flight.target)
	draw_circle(pos, size * (0.5 + t), Color(1, 1, 1, 0.35 * (1.0 - t)))
	for k in 8:
		var dir := Vector2.RIGHT.rotated(TAU * k / 8.0 + 0.3)
		draw_line(pos + dir * size * 0.4, pos + dir * size * (0.8 + t), c, 4.0)


func _draw_ball(p: float) -> void:
	var q := persp(p)
	var pos := RELEASE.lerp(zone_to_screen(flight.zone_pos(p)), q)
	var r := lerpf(3.0, 14.0, q)
	draw_circle(pos, r, Color("#f4f1e8"))
	draw_spin(self, pos, r, flight.name, float(now() - flight.release_usec) / 1e6)


## 회전 그림 (과장, 3.1절 "공 회전으로 힌트"). 계열 그림 5개 + 기울기·빠르기.
static func draw_spin(c: CanvasItem, pos: Vector2, r: float, p_name: String, t_sec: float) -> void:
	var d: Dictionary = PitchTypes.LIST[p_name]
	var ang: float = TAU * float(d["rps"]) * t_sec
	var tilt: float = d["tilt"]
	var red := Color("#c8302c")
	match d["spin"]:
		"stripe_v", "sweep":
			# 줄무늬 두 줄이 회전 방향으로 흐름. 패스트볼 = 세로(역회전), 스위퍼 = 옆으로 돔
			var axis := Vector2(0, 1).rotated(tilt) if d["spin"] == "stripe_v" else Vector2(1, 0)
			var across := axis.orthogonal()
			for k in 2:
				var off := fposmod(ang / TAU + k * 0.5, 1.0) * 2.0 - 1.0
				var w := sqrt(maxf(0.0, 1.0 - off * off)) * r * 0.9
				var cpos := pos + across * off * r * 0.8
				c.draw_line(cpos - axis * w, cpos + axis * w, red, maxf(1.0, r * 0.18))
		"dot":
			# 빨간 점: 회전축이 화면을 향함 → 점이 제자리에서 돎
			c.draw_circle(pos, r * 0.32, red)
			c.draw_arc(pos, r * 0.62, ang, ang + PI * 0.9, 8, red, maxf(1.0, r * 0.12))
		"roll":
			# 앞으로 도는 회전: 실밥이 위에서 아래로 흐름 (기울기 tilt)
			var axis2 := Vector2(1, 0).rotated(tilt)
			var down := axis2.orthogonal() * -1.0
			for k in 2:
				var off2 := fposmod(-ang / TAU + k * 0.5, 1.0) * 2.0 - 1.0
				var w2 := sqrt(maxf(0.0, 1.0 - off2 * off2)) * r * 0.9
				var cp := pos + down * off2 * r * 0.8
				c.draw_line(cp - axis2 * w2, cp + axis2 * w2, red, maxf(1.0, r * 0.18))
		"slow":
			# 느린 회전·거의 무회전: 실밥 곡선이 천천히 돎 (포크볼은 거의 안 돎)
			c.draw_arc(pos + Vector2(r * 0.55, 0).rotated(ang), r * 0.55, ang + PI * 0.6, ang + PI * 1.4, 10, red, maxf(1.0, r * 0.14))
			c.draw_arc(pos - Vector2(r * 0.55, 0).rotated(ang), r * 0.55, ang - PI * 0.4, ang + PI * 0.4, 10, red, maxf(1.0, r * 0.14))
