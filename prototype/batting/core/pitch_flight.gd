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


## 도착 시간은 표시 구속(km/h)으로 계산 (2026-11-18 KAL 피드백: 체감 속도 = 도착 시간이라, 표시 구속과 맞아야 함).
## base_ms: 145km/h(구속 50 포심)의 도착 시간 (조절판, 시작 650ms)
## slow: 선구 대결 느려짐 (1단계 모델 값, 시간 × (1 + slow))
## speed_gamma: 속도 차이 과장 (1 = 구속에 정비례, 2 = 차이를 2배로 느끼게). 조절판
## break_scale: 화면의 휘는 크기 배율 (조절판)
func setup(p_name: String, loc: Dictionary, base_ms: float, now_usec: int, brk_stat: float = 50.0, vel_stat: float = 50.0,
		slow: float = 0.0, speed_gamma: float = 1.0, break_scale: float = 1.0) -> void:
	name = p_name
	target = Vector2(loc["x"], loc["y"])
	kind = loc.get("kind", "normal")
	move = PitchTypes.movement(name, brk_stat) * break_scale
	if kind == "center":
		move *= 0.5            # 한가운데 실투는 무브먼트도 줄어듦 (3.1절, 줄어드는 폭은 미정 → 시작값 절반)
	var ratio: float = PitchTypes.LIST[name]["ratio"]
	# 구속 → km/h 환산은 아직 안 정함 (성장·등급 뒤). 시험판 임시: 구속 50 포심 = 145km/h, 1점당 0.3km/h.
	kmh = roundf(145.0 * ratio + (vel_stat - 50.0) * 0.3)
	travel_ms = travel_time(base_ms, kmh, slow, speed_gamma)
	release_usec = now_usec
	arrive_usec = now_usec + int(travel_ms * 1000.0)


## 도착 시간 = 145km/h 기준 시간 × (145 / 구속)^과장 × (1 + 느려짐). 예) 175km/h → 650 × 145/175 = 539ms
static func travel_time(base_ms: float, kmh_val: float, slow: float = 0.0, speed_gamma: float = 1.0) -> float:
	return base_ms * pow(145.0 / maxf(kmh_val, 60.0), speed_gamma) * (1.0 + slow)


## 화면에서 공 위치 (원근 적용). 휘는 폭은 원근으로 줄이지 않고 화면 크기 그대로 더함 (2026-11-18 버그 수정:
## 전에는 원근으로 줄인 뒤 더해서 커브도 직선과 최대 8px 차이뿐이라 변화가 안 보였음).
## to_screen: 존 좌표 → 화면 좌표, persp_q: 원근 진행도
func screen_pos(p: float, release: Vector2, to_screen: Callable, persp_q: float) -> Vector2:
	var k: float = PitchTypes.LIST[name]["brk"]
	var start: Vector2 = to_screen.call(target - move)     # 휘지 않았다면 갔을 곳
	var end: Vector2 = to_screen.call(target)              # 실제 도착 위치
	# 휘는 정도는 시간(p)이 아니라 화면에서 다가온 정도(persp_q) 기준: 공이 처음 향하던 곳 쪽으로 오다가
	# 가까워진 뒤에 꺾이게 (시간 기준이면 공이 아직 멀리 있을 때 다 휘어서 처음 방향과 상쇄돼 직선처럼 보였음)
	return release.lerp(start, persp_q) + (end - start) * pow(persp_q, k)


## 진행도 0(손) ~ 1(미트)
func progress(now_usec: int) -> float:
	return clampf(float(now_usec - release_usec) / float(arrive_usec - release_usec), 0.0, 1.0)


## 진행도 p에서 공이 향하는 존 위 위치 (존 단위)
func zone_pos(p: float) -> Vector2:
	var k: float = PitchTypes.LIST[name]["brk"]
	return target - move * (1.0 - pow(p, k))
