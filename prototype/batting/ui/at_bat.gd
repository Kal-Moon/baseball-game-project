## 2단계 타석 화면 (도형). docs/game-design.md 4.1절 표 2단계.
## 존 테두리, 날아오는 공(원근 + 회전 그림), 스와이프 입력(터치 시각 기준), 투구 뒤 표시.
## AI 투수(랜덤 투수·볼배합)는 3단계, 결과 판정·조절판은 4단계라 여기서는 구종·코스만 랜덤.
extends Node2D

const Model := preload("res://core/batting_model.gd")
const PitchTypes := preload("res://core/pitch_types.gd")
const Flight := preload("res://core/pitch_flight.gd")
const SwingInput := preload("res://core/swing_input.gd")

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
var base_ms := 650.0                    # 포심 도착 시간 (조절판은 4단계)
var right_batter := true

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
	_enter(State.WAIT, 800)


func _enter(s: State, ms: int) -> void:
	state = s
	state_until = now() + ms * 1000


func _process(_dt: float) -> void:
	tick()
	queue_redraw()


func tick() -> void:
	var t := now()
	match state:
		State.WAIT:
			if t >= state_until:
				_enter(State.WINDUP, 600)
		State.WINDUP:
			if t >= state_until:
				throw_pitch(PitchTypes.NAMES[model.rng.randi_range(0, PitchTypes.NAMES.size() - 1)],
					model.pitch_location(0, 0))
		State.FLIGHT:
			if t >= flight.arrive_usec + int(input.late_cutoff * 1000.0):
				_finish_pitch()
		State.SHOW:
			if t >= state_until:
				_enter(State.WAIT, 300)


func throw_pitch(p_name: String, loc: Dictionary) -> void:
	flight.setup(p_name, loc, base_ms, now())
	touch_usec = -1
	swing = ""
	level = null
	bat_start = -1
	contact = ""
	flash_start = -1
	state = State.FLIGHT


## ---- 입력: 손가락이 닿은 시각이 타이밍, 이어지는 움직임이 스윙 종류 ----

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed:
			on_touch_down(event.position, now())
		else:
			on_touch_up(event.position)
	elif event is InputEventScreenDrag:
		on_drag(event.position)


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
	if level == null:
		var zone := Model.in_zone(flight.target.x, flight.target.y)
		last_text = pitch_info
		last_sub = "스트라이크" if zone else "볼"
	else:
		last_text = "%s · %s" % [SwingInput.TIMING_NAMES[level], pitch_info]
		var c := input.compat(flight.target.x, flight.target.y, swing)
		last_sub = "%s (%+d ms)" % [swing, roundi(float(touch_usec - flight.arrive_usec) / 1000.0)]
		last_sub += ["  궁합 좋음", "", "  반대 스윙"][c]     # 시험판 확인용. 실제 게임은 궁합을 표시하지 않음 (3.1절)
	_enter(State.SHOW, 1500)


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
	var info := ThemeDB.fallback_font
	draw_string(info, Vector2(16, 30), "타격 시험판 2단계 · 탭=레벨  위=어퍼  아래=다운  ←=당겨치기  →=밀어치기 (우타자)", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(1, 1, 1, 0.7))


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
