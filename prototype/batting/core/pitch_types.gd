## 기본 구종 11개 (docs/game-design.md 2.3절 "투수 구종" 표, 4.1절 "넣을 구종").
## 방향은 투수 기준: arm(+) = 던지는 팔 쪽, glove(-) = 반대. 오른손 투수 기준 화면에서는
## 팔 쪽 = 우타자 몸쪽(x < 0). 크기 1~5는 2.3절 기준값. ★ 값은 문서에서도 추정값.
## 화면용 숫자(크기 1 = 존 단위 얼마, 꺾이는 시점 지수)는 시험판 시작값 (근거 없는 추정, 조절 대상).
extends RefCounted

## spin: 회전 그림 계열 (2.3절 "회전 그림은 계열 그림 5개 + 변형")
##   stripe_v  줄무늬(패스트볼 계열, tilt로 기울기)   dot  빨간 점(슬라이더류)
##   sweep     옆으로 도는 줄무늬(스위퍼)             roll 앞으로 도는 회전(커브류)
##   slow      느린 회전·거의 무회전(오프스피드)
## rps: 화면 회전 빠르기 (초당 바퀴, 과장된 값)
## brk: 꺾이는 시점 지수. 클수록 늦게 꺾임 (1.5 일찍 ~ 4 늦게 뚝)
const LIST := {
	"포심":       {"ratio": 1.00, "dx": 0.0,  "dy": 0.3,  "size": 1, "brk": 2.0, "spin": "stripe_v", "tilt": 0.0,  "rps": 6.0},
	"싱커":       {"ratio": 1.00, "dx": 0.7,  "dy": -0.7, "size": 3, "brk": 2.5, "spin": "stripe_v", "tilt": 0.6,  "rps": 5.5},
	"커터":       {"ratio": 0.95, "dx": -1.0, "dy": 0.0,  "size": 1, "brk": 3.5, "spin": "stripe_v", "tilt": 0.25, "rps": 5.5},
	"슬라이더":   {"ratio": 0.91, "dx": -0.9, "dy": -0.4, "size": 3, "brk": 3.5, "spin": "dot",      "tilt": 0.0,  "rps": 5.0},
	"스위퍼":     {"ratio": 0.88, "dx": -1.0, "dy": -0.1, "size": 5, "brk": 1.8, "spin": "sweep",    "tilt": 0.0,  "rps": 5.0},
	"커브":       {"ratio": 0.85, "dx": -0.5, "dy": -0.9, "size": 4, "brk": 1.6, "spin": "roll",     "tilt": 0.3,  "rps": 3.5},
	"너클커브":   {"ratio": 0.87, "dx": -0.5, "dy": -0.9, "size": 4, "brk": 3.5, "spin": "roll",     "tilt": 0.3,  "rps": 5.0},
	"체인지업":   {"ratio": 0.92, "dx": 0.3,  "dy": -1.0, "size": 2, "brk": 2.5, "spin": "stripe_v", "tilt": 0.0,  "rps": 2.5},
	"서클체인지업": {"ratio": 0.90, "dx": 0.6, "dy": -0.8, "size": 3, "brk": 2.5, "spin": "slow",     "tilt": 0.5,  "rps": 2.0},
	"스플리터":   {"ratio": 0.91, "dx": 0.0,  "dy": -1.0, "size": 3, "brk": 4.0, "spin": "slow",     "tilt": 0.0,  "rps": 1.6},
	"포크볼":     {"ratio": 0.89, "dx": 0.0,  "dy": -1.0, "size": 4, "brk": 4.0, "spin": "slow",     "tilt": 0.0,  "rps": 0.7},
}

const NAMES := ["포심", "싱커", "커터", "슬라이더", "스위퍼", "커브", "너클커브", "체인지업", "서클체인지업", "스플리터", "포크볼"]

## 크기 1 = 존 단위 0.12 (존 폭 2 기준. 크기 5 = 0.6, 존의 30%). 화면에서는 조절판 "변화 크기" 배율(시작 2.0)을 곱함.
const SIZE_UNIT := 0.12


## 변화 능력치 반영 전 움직임 (존 단위). 오른손 투수: 팔 쪽 = x 음수(우타자 몸쪽).
static func movement(name: String, brk_stat: float = 50.0, right_handed_pitcher: bool = true) -> Vector2:
	var d: Dictionary = LIST[name]
	var v := Vector2(d["dx"], d["dy"])
	if v.length() > 0.0:
		v = v.normalized()
	var arm_sign := -1.0 if right_handed_pitcher else 1.0
	var scale: float = d["size"] * SIZE_UNIT * (brk_stat / 50.0)   # "실제 크기 = 기준값 × 변화 능력치"
	return Vector2(v.x * arm_sign * scale, v.y * scale)
