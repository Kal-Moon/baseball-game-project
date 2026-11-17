## 타격 입력 판정 (화면과 분리, 4장 원칙). docs/game-design.md 3.1절 "타격", "타이밍 판정 (7단계)".
## - 타이밍은 손가락이 닿은 시각으로만 판정, 이어지는 움직임은 스윙 종류만 읽음.
## - 탭 = 레벨, 위 = 어퍼, 아래 = 다운, 좌·우 = 화면상 타구 방향 (우타자는 왼쪽이 당겨치기).
## 숫자는 모두 시험판 시작값 (추정, 조절판·기록으로 고침).
extends RefCounted

const SWINGS := ["레벨", "어퍼", "다운", "당겨치기", "밀어치기"]
## 7단계: -3 너무 빠름 … 0 완벽 … +3 너무 늦음
const TIMING_NAMES := {-3: "너무 빠름", -2: "빠름", -1: "좋음 ◀", 0: "완벽!", 1: "좋음 ▶", 2: "늦음", 3: "너무 늦음"}

## 구간 폭 (ms, 완벽 위치에서 한쪽으로). 시작값: 5.5절 "보통 유저" 타이밍 분포(너무 25% · 빠름/늦음 35% ·
## 좋음 30% · 완벽 10%)가 터치 오차 표준편차 약 60ms일 때 나오도록 잡은 값. 60ms는 근거 없는 가정.
var w_perfect := 10.0
var w_good := 30.0
var w_near := 70.0
## 미트 도착 뒤 이 시간까지만 늦은 스윙, 그 뒤 입력은 무시 (3.1절 "예: 0.2초")
var late_cutoff := 200.0
## 스윙마다 "완벽" 위치 (ms, 음수 = 일찍). 당겨치기 일찍, 밀어치기 늦게 (3.1절). 폭은 추정.
var swing_offset := {"레벨": 0.0, "어퍼": 0.0, "다운": 0.0, "당겨치기": -15.0, "밀어치기": 15.0}
## 스와이프 인식: 이 거리(화면 높이 대비) 미만이면 탭
var swipe_min := 0.04
## 가운데 원 반지름 (존 단위, 존 반폭 = 1). 코스 궁합용 시작값 추정.
var center_radius := 0.35


## 손가락 움직임(화면 좌표, 아래가 +y) → 스윙 종류
func classify_swipe(delta: Vector2, screen_h: float, right_batter: bool = true) -> String:
	if delta.length() < swipe_min * screen_h:
		return "레벨"
	if absf(delta.y) >= absf(delta.x):
		return "어퍼" if delta.y < 0 else "다운"
	var left := delta.x < 0
	# 우타자: 화면 왼쪽(3루 쪽)이 당겨치기
	if left == right_batter:
		return "당겨치기"
	return "밀어치기"


## 터치 시각과 공 도착 시각(둘 다 usec) → 7단계 (-3~3). 무시할 입력이면 null.
func timing_level(touch_usec: int, arrive_usec: int, swing: String):
	var e := float(touch_usec - arrive_usec) / 1000.0 - float(swing_offset.get(swing, 0.0))
	if e > late_cutoff:
		return null
	var a := absf(e)
	var lv := 3
	if a <= w_perfect: lv = 0
	elif a <= w_good: lv = 1
	elif a <= w_near: lv = 2
	return lv if e > 0 else -lv


## 7단계 → batting_model 의 4단계 (0 너무 ~ 3 완벽)
static func grade(level: int) -> int:
	return 3 - absi(level)


## 코스·스윙 궁합 (3.1절 X자 4구역 + 가운데 원). 반환: 0 좋음 / 1 보통 / 2 나쁨
## x < 0 = 타자 몸쪽 (batting_model 좌표와 같음), y > 0 = 높은 공
func compat(x: float, y: float, swing: String) -> int:
	if Vector2(x, y).length() <= center_radius:
		return 0 if swing == "레벨" else 1
	var region := ""
	if absf(y) >= absf(x):
		region = "위" if y > 0 else "아래"
	else:
		region = "몸쪽" if x < 0 else "바깥쪽"
	var good := {"위": "다운", "아래": "어퍼", "몸쪽": "당겨치기", "바깥쪽": "밀어치기"}
	var bad := {"위": "어퍼", "아래": "다운", "몸쪽": "밀어치기", "바깥쪽": "당겨치기"}
	if swing == good[region]: return 0
	if swing == bad[region]: return 2
	return 1
