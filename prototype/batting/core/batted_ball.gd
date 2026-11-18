## 4단계 인플레이 타구 표현 (화면과 분리). docs/game-design.md 4.1절 "결과": 타구는 방향·질로 안타·아웃을 판정해
## 글자와 간단한 궤적으로. 안타·아웃 자체는 1단계 모델(batting_model.ball_in_play)이 정하고,
## 여기서는 그 결과를 "좌중간 2루타", "유격수 땅볼"처럼 보여 줄 방향·글자·거리만 정함.
## 방향 규칙(3.1절): 스윙 종류가 방향을 정함 (우타자 당겨치기 = 왼쪽), 빠른 타이밍은 당겨친 쪽, 늦으면 밀어친 쪽.
## 각도·거리 숫자는 시험판 표현용 시작값 (추정).
extends RefCounted


## 타구 각도 (도, -45 = 3루 선, 0 = 가운데, +45 = 1루 선). 우타자 기준.
static func angle(swing: String, level: int, rng: RandomNumberGenerator, right_batter: bool = true) -> float:
	var base := 0.0
	if swing == "당겨치기": base = -25.0
	elif swing == "밀어치기": base = 25.0
	var a := base + 8.0 * float(level) + rng.randfn(0.0, 12.0)     # level < 0 (빠름) → 당겨친 쪽
	a = clampf(a, -44.0, 44.0)
	return a if right_batter else -a


static func field_part(a: float) -> String:
	if a < -27.0: return "좌측"
	if a < -9.0: return "좌중간"
	if a <= 9.0: return "중앙"
	if a <= 27.0: return "우중간"
	return "우측"


## 결과 글자와 궤적 정보. outcome: HR / 3B / 2B / 1B / OUT, quality: weak / normal / strong
static func describe(outcome: String, quality: String, swing: String, a: float, rng: RandomNumberGenerator) -> Dictionary:
	var part := field_part(a)
	var text := ""
	var dist := 0.0          # 1.0 = 담장
	var fly := true          # 뜬공(포물선) / 땅볼(직선)
	match outcome:
		"HR":
			text = "%s 홈런" % ("가운데 담장 넘는" if part == "중앙" else part); dist = 1.15
		"3B":
			text = "%s 3루타" % part; dist = 0.95
		"2B":
			text = "%s 2루타" % part; dist = 0.85
		"1B":
			var side := "좌전" if a < -12.0 else ("우전" if a > 12.0 else "중전")
			text = side + " 안타"; dist = 0.55; fly = quality != "weak"
		_:
			var ground := false
			if swing == "어퍼": ground = rng.randf() < 0.2
			elif swing == "다운": ground = rng.randf() < 0.75
			else: ground = rng.randf() < (0.6 if quality == "weak" else 0.45)
			if ground:
				var pos := "3루수" if a < -22.0 else ("유격수" if a < 0.0 else ("2루수" if a < 22.0 else "1루수"))
				text = pos + " 땅볼"; dist = 0.3; fly = false
			elif quality == "weak":
				var pos2 := "3루수" if a < -15.0 else ("1루수" if a > 15.0 else "유격수")
				text = pos2 + " 뜬공 (내야)"; dist = 0.35
			else:
				var of := "좌익수" if a < -15.0 else ("우익수" if a > 15.0 else "중견수")
				var liner := quality == "strong" or rng.randf() < 0.3
				text = of + (" 직선타" if liner else " 뜬공"); dist = 0.75 if liner else 0.8
	return {"text": text, "dist": dist, "angle": a, "fly": fly, "hit": outcome != "OUT"}
