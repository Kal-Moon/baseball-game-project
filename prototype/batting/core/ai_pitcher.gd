## 3단계 AI 투수 (화면과 분리). docs/game-design.md 4.1절 "넣을 구종", 2.3절 "처음 구종"·"구종 등급".
## - 타석마다 랜덤 투수: 구종 수 비율, 패스트볼 계열(포심·싱커·커터) 1개 필수, 한국 리그 구종 확률. 특수 구종 뺌.
## - 볼배합: 볼카운트별 패스트볼 계열 비율 = MLB 2025 실제 값 (docs/research/pitch-level.md 3장).
##   존 안·밖은 1단계 모델(batting_model.pitch_location)의 카운트 규칙 그대로 (KBO 2026에 맞춘 값).
extends RefCounted

const FASTBALLS := ["포심", "싱커", "커터"]
## 한국 리그 구종 확률 (2.3절 표, 그 구종을 가진 투수 %). 체인지업 칸에서 서클체인지업을 같이 뽑음.
const PROB := {"포심": 85.0, "싱커": 54.0, "커터": 30.0, "슬라이더": 55.0, "스위퍼": 3.0, "커브": 29.0,
	"너클커브": 7.0, "체인지업": 42.0, "스플리터": 11.0, "포크볼": 4.0}
## 실제로 뽑을 때 쓰는 가중치. PROB를 그대로 쓰면 "패스트볼 1개 먼저" 단계 때문에 싱커·커터가 너무 많이 나와서
## (싱커 67%, 커터 46%), 결과가 PROB 비율대로 나오도록 반복 계산으로 맞춘 값 (2026-11-18).
## 주의: PROB 합 322%는 구종 수 비율의 평균 3.52개(352%)보다 작음 (스위퍼를 32% → 3%로 줄인 만큼).
## 구종 수 비율을 지키면 모든 구종이 PROB보다 약 9% 더 나옴 (예: 포심 93%, 슬라이더 60%) → KAL 확인 대기.
const DRAW_W := {"포심": 9.6, "싱커": 2.9, "커터": 1.3, "슬라이더": 4.3, "스위퍼": 0.2, "커브": 1.7,
	"너클커브": 0.4, "체인지업": 2.8, "스플리터": 0.6, "포크볼": 0.2}
## 체인지업 칸에서 서클체인지업이 나오는 비율. 자료 없음 → 시험판 시작값 30% (추정 ★)
const CIRCLE_SHARE := 0.3
## 구종 수 비율 2개 15% · 3개 35% · 4개 35% · 5개 13% · 6개 2% (2.3절)
const COUNT_W := {2: 15.0, 3: 35.0, 4: 35.0, 5: 13.0, 6: 2.0}
## 볼카운트(볼-스트라이크)별 패스트볼 계열 비율, MLB 2025 (pitch-level.md 3장)
const FB_SHARE := {
	"0-0": 0.602, "0-1": 0.497, "0-2": 0.419, "1-0": 0.595, "1-1": 0.500, "1-2": 0.433,
	"2-0": 0.703, "2-1": 0.583, "2-2": 0.481, "3-0": 0.935, "3-1": 0.764, "3-2": 0.621,
}
## 구종 등급 (2.3절): 원 배율과 뽑는 확률. 패스트볼·커브 계열은 문서 값, 나머지는 "그 사이" → 시작값 추정 ★
const GRADE_MULT := {"S": 0.85, "A": 0.92, "B": 1.00, "C": 1.08, "D": 1.15}
const GRADE_W_FB := {"S": 5.0, "A": 20.0, "B": 50.0, "C": 20.0, "D": 5.0}
const GRADE_W_CURVE := {"S": 2.0, "A": 13.0, "B": 45.0, "C": 30.0, "D": 10.0}
const GRADE_W_OTHER := {"S": 3.0, "A": 17.0, "B": 48.0, "C": 25.0, "D": 7.0}
const CURVES := ["커브", "너클커브"]

var rng: RandomNumberGenerator
var pitches: Array = []       # 이 투수의 구종 (첫 번째가 주 패스트볼)
var grades: Dictionary = {}   # 구종 → 등급
var locked := ""              # 조절판: 구종 하나만 던지게 고정 ("" = 고정 안 함)


func _init(r: RandomNumberGenerator) -> void:
	rng = r


func _pick_key(w: Dictionary) -> Variant:
	var total := 0.0
	for k in w: total += float(w[k])
	var x := rng.randf() * total
	for k in w:
		x -= float(w[k])
		if x < 0.0: return k
	return w.keys().back()


## 새 투수 만들기
func new_pitcher() -> void:
	var n: int = _pick_key(COUNT_W)
	# ① 패스트볼 계열 1개 (확률 비례)
	var fb := {}
	for f in FASTBALLS: fb[f] = DRAW_W[f]
	var first: String = _pick_key(fb)
	pitches = [first]
	# ② 나머지는 남은 구종에서 확률 비례로 겹치지 않게 (다른 패스트볼 계열도 가능, 예: 포심 + 싱커)
	var pool := DRAW_W.duplicate()
	pool.erase(first)
	while pitches.size() < n and pool.size() > 0:
		var p: String = _pick_key(pool)
		pool.erase(p)
		if p == "체인지업" and rng.randf() < CIRCLE_SHARE:
			p = "서클체인지업"
		pitches.append(p)
	grades = {}
	for p in pitches:
		var w: Dictionary = GRADE_W_FB if p in FASTBALLS else (GRADE_W_CURVE if p in CURVES else GRADE_W_OTHER)
		grades[p] = _pick_key(w)


func is_fastball(p: String) -> bool:
	return p in FASTBALLS


## 볼배합: 이번 공의 구종
func choose_pitch(balls: int, strikes: int) -> String:
	if locked != "":
		return locked
	var fbs := pitches.filter(func(p): return p in FASTBALLS)
	var others := pitches.filter(func(p): return not (p in FASTBALLS))
	if others.is_empty(): return fbs[rng.randi_range(0, fbs.size() - 1)]
	var share: float = FB_SHARE["%d-%d" % [mini(balls, 3), mini(strikes, 2)]]
	if rng.randf() < share:
		return fbs[rng.randi_range(0, fbs.size() - 1)]
	return others[rng.randi_range(0, others.size() - 1)]


## 이 구종의 원 배율 (등급). 고정 구종이 이 투수에게 없으면 B.
func circle_mult(p: String) -> float:
	return GRADE_MULT[grades.get(p, "B")]
