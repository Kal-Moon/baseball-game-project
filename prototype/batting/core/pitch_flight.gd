## 공 하나의 비행 (화면과 분리). 시간은 실제 시각(usec)으로 계산해 프레임과 무관하게 함 (4.1절).
## 공은 처음에 "target - 움직임" 쪽으로 오는 것처럼 보이다가 꺾이는 시점(brk 지수)에 따라 target으로 감.
extends RefCounted

const PitchTypes := preload("res://core/pitch_types.gd")

var name := "포심"
var target := Vector2.ZERO        # 도착 위치 (존 단위, x < 0 몸쪽, y > 0 높은 공)
var move := Vector2.ZERO          # 움직임 (존 단위)
var kind := "normal"              # normal / center(한가운데 실투) / wild(빠진 공)
var travel_ms := 650.0            # 손에서 미트까지
var release_usec := 0
var arrive_usec := 0
var kmh := 0.0


## base_ms: 포심(구속 50) 도착 시간 (조절판, 시작 650ms, 4.1절)
func setup(p_name: String, loc: Dictionary, base_ms: float, now_usec: int, brk_stat: float = 50.0, vel_stat: float = 50.0) -> void:
	name = p_name
	target = Vector2(loc["x"], loc["y"])
	kind = loc.get("kind", "normal")
	move = PitchTypes.movement(name, brk_stat)
	if kind == "center":
		move *= 0.5            # 한가운데 실투는 무브먼트도 줄어듦 (3.1절, 줄어드는 폭은 미정 → 시작값 절반)
	var ratio: float = PitchTypes.LIST[name]["ratio"]
	travel_ms = base_ms / ratio
	release_usec = now_usec
	arrive_usec = now_usec + int(travel_ms * 1000.0)
	# 구속 → km/h 환산은 아직 안 정함 (성장·등급 뒤). 시험판 표시용 임시: 구속 50 포심 = 145km/h.
	kmh = roundf(145.0 * ratio + (vel_stat - 50.0) * 0.3)


## 진행도 0(손) ~ 1(미트)
func progress(now_usec: int) -> float:
	return clampf(float(now_usec - release_usec) / float(arrive_usec - release_usec), 0.0, 1.0)


## 진행도 p에서 공이 향하는 존 위 위치 (존 단위)
func zone_pos(p: float) -> Vector2:
	var k: float = PitchTypes.LIST[name]["brk"]
	return target - move * (1.0 - pow(p, k))
