## 타석 계산 부분 (화면과 분리, 4장 원칙). simulation/direct_play_sim.py를 옮김.
## 실제 게임: 타이밍 단계·코스 궁합은 유저 입력, 공 느려짐·빨라짐은 실제 도착 시간으로 반영 (timing_mods = false).
## 테스트:     타이밍 단계·궁합을 유저 세 단계 분포에서 뽑고, 느려짐·구속 효과를 확률로 반영 (timing_mods = true).
extends RefCounted

const Params := preload("res://core/params.gd")

var rng := RandomNumberGenerator.new()
var outcome := {}          # SKILL_BLEND 적용한 타이밍 단계별 결과표

# 능력치에서 계산한 효과 (set_stats로 정함)
var slow := 0.0            # 선구 대결 느려짐 (+면 느려짐)
var late := 0.0            # 구속: 타이밍 늦어짐 확률
var ce := 0.0              # 정확 맞대결 효과
var be := 0.0              # 변화 장타 억제
var pl := 0.0              # 파워 맞대결 값 (점)
var se := 0.0              # 구위 먹힌 타구
var hr_mult := 1.0
var sigma := 0.42
var miss := 0.03
var body_x := -2.13


func _init(seed_value: int = 1) -> void:
	rng.seed = seed_value
	_build_outcome()
	set_stats({})


func _build_outcome() -> void:
	var w: Array = Params.USERS["보통"]["timing"]
	var avg := []
	for i in 5:
		var s := 0.0
		for gi in 4:
			s += w[gi] * Params.BASE_OUTCOME[Params.GRADES[gi]][i]
		avg.append(s)
	for g in Params.GRADES:
		var row := []
		for i in 5:
			row.append(Params.SKILL_BLEND * Params.BASE_OUTCOME[g][i] + (1.0 - Params.SKILL_BLEND) * avg[i])
		outcome[g] = row


static func _clamp(v: float, lo: float, hi: float) -> float:
	return maxf(lo, minf(hi, v))


## 능력치: eye(선구) con(정확) pw(파워) / vel(구속) brk(변화) st(구위) ctl(제구). 없으면 50.
func set_stats(s: Dictionary) -> void:
	var eye: float = s.get("eye", 50); var con: float = s.get("con", 50); var pw: float = s.get("pw", 50)
	var vel: float = s.get("vel", 50); var brk: float = s.get("brk", 50); var st: float = s.get("st", 50)
	var ctl: float = s.get("ctl", 50)
	var E := Params.EYE; var V := Params.VEL; var C := Params.CON; var B := Params.BRK
	var PW := Params.POW; var S := Params.STF; var T := Params.CTL
	slow = _clamp(E["coef"] * ((eye - 50) - V["eye_w"] * (vel - 50)), E["cap_fast"], E["cap_slow"])
	late = V["late"] * _clamp(vel - 50, V["cap_neg"], V["cap_pos"])
	if late < 0: late *= V["neg_scale"]
	ce = C["coef"] * _clamp((con - 50) - C["brk_weight"] * (brk - 50) - C["stuff_weight"] * (st - 50), C["cap_neg"], C["cap_pos"])
	be = B["coef"] * _clamp(brk - 50, B["cap_neg"], B["cap_pos"])
	if be < 0: be *= B["neg_scale"]
	pl = _clamp((pw - 50) - PW["stuff_weight"] * (st - 50), PW["cap_neg"], PW["cap_pos"])
	se = S["coef"] * _clamp(st - 50, S["cap_neg"], S["cap_pos"])
	if se < 0: se *= S["neg_scale"]
	hr_mult = maxf(0.0, 1.0 + PW["hr"] * pl)
	var c := _clamp(ctl - 50, T["cap_neg"], T["cap_pos"])
	if c < 0: c *= T["neg_scale"]
	sigma = Params.P["sigma"] * (1.0 - T["circle"] * c)
	miss = Params.P["miss"] * maxf(0.0, 1.0 - T["miss"] * c)
	body_x = Params.P["body_x"] + (T["body"] if c >= 0 else T["body_neg"]) * c


func pick(weights: Array) -> int:
	var total := 0.0
	for w in weights: total += w
	var r := rng.randf() * total
	for i in weights.size():
		r -= weights[i]
		if r < 0: return i
	return weights.size() - 1


func _sign() -> int:
	return -1 if rng.randf() < 0.5 else 1


## AI 투수의 공 위치. 좌표는 존을 -1~1로 둔 단위, x < 0 이 타자 몸쪽. kind: normal / center(한가운데 실투) / wild(빠진 공)
func pitch_location(balls: int, strikes: int) -> Dictionary:
	var P := Params.P
	if rng.randf() < miss:
		if rng.randf() < P["miss_center"]:
			return {"x": rng.randfn(0, 0.2), "y": rng.randfn(0, 0.2), "kind": "center"}
		return {"x": _sign() * rng.randf_range(1.8, 2.6), "y": rng.randf_range(-1.5, 1.5), "kind": "wild"}
	var aim: float = P["aim_zone"] + (0.2 if balls == 3 else 0.0) - (0.12 if strikes == 2 and balls < 2 else 0.0)
	var ax: float; var ay: float
	if rng.randf() < aim:
		ax = rng.randf_range(-0.85, 0.85); ay = rng.randf_range(-0.85, 0.85)
	elif rng.randf() < 0.5:
		ax = _sign() * rng.randf_range(1.15, 1.5); ay = rng.randf_range(-1, 1)
	else:
		ax = rng.randf_range(-1, 1); ay = _sign() * rng.randf_range(1.15, 1.5)
	return {"x": ax + rng.randfn(0, sigma), "y": ay + rng.randfn(0, sigma), "kind": "normal"}


static func in_zone(x: float, y: float) -> bool:
	return absf(x) <= 1.0 and absf(y) <= 1.0


func is_hbp(x: float) -> bool:
	return x < body_x


## 스윙 결과. grade: 0 너무 ~ 3 완벽, compat: 0 좋음 / 1 보통 / 2 나쁨. 반환: [결과, 최종 타이밍 단계]
func resolve_swing(grade: int, zone: bool, kind: String, compat: int, timing_mods: bool) -> Array:
	var g := grade
	if timing_mods:
		if slow > 0 and rng.randf() < Params.EYE["timing"] * slow: g = mini(3, g + 1)
		elif slow < 0 and rng.randf() < -Params.EYE["timing"] * slow: g = maxi(0, g - 1)
		if late > 0 and rng.randf() < late: g = maxi(0, g - 1)
		elif late < 0 and rng.randf() < -late: g = mini(3, g + 1)
	if not zone and rng.randf() < Params.P["out_zone_penalty"]: g = maxi(0, g - 1)
	if kind == "center": g = mini(3, g + 1)
	var res: String = Params.RESULTS[pick(outcome[Params.GRADES[g]])]
	if not zone and res != "whiff" and rng.randf() < Params.P["out_zone_whiff"]: res = "whiff"
	if late != 0 and res == "foul" and rng.randf() < absf(late) * Params.VEL["whiff"]:
		if late > 0: res = "whiff"
	elif late < 0 and res == "whiff" and rng.randf() < -late * Params.VEL["whiff"]:
		res = "foul"
	var missed := g <= 1 or not zone
	var C := Params.CON
	if missed and ce > 0:
		if res == "whiff" and rng.randf() < ce:
			res = "foul" if rng.randf() < C["to_foul"] else "weak"
		elif g == 1 and res == "weak" and rng.randf() < ce * C["upgrade"]:
			res = "normal"
	elif missed and ce < 0:
		if (res == "foul" or res == "weak") and rng.randf() < -ce * C["neg_whiff"]:
			res = "whiff"
		elif g == 1 and res == "normal" and rng.randf() < -ce * C["neg_down"]:
			res = "weak"
	if res == "weak" or res == "normal" or res == "strong":
		var order := ["weak", "normal", "strong"]
		var bad_p := 0.5 * Params.COMPAT_EFFECT * (1.0 - _clamp(ce, -1, 1))
		var i := order.find(res)
		if compat == 0 and rng.randf() < 0.3 * Params.COMPAT_EFFECT: i += 1
		elif compat == 2 and rng.randf() < bad_p: i -= 1
		if be > 0 and i == 2 and rng.randf() < be: i = 1
		elif be < 0 and i == 1 and rng.randf() < -be: i = 2
		i = clampi(i, 0, 2)
		var up: float = Params.POW["up"] * pl * Params.TIMING_W[g]
		if up > 0 and i == 1 and rng.randf() < up: i = 2
		elif up < 0 and i == 2 and rng.randf() < -up * Params.POW["neg_up"]: i = 1
		if se > 0 and i == 1 and rng.randf() < se: i = 0
		elif se < 0 and i == 0 and rng.randf() < -se: i = 1
		res = order[i]
	return [res, g]


## 맞힌 타구 → HR / 3B / 2B / 1B / OUT
func ball_in_play(q: String) -> String:
	var t: Array = Params.P[q]
	if rng.randf() < t[3] * hr_mult: return "HR"
	if rng.randf() < t[0]:
		var r := rng.randf()
		if r < t[2]: return "3B"
		if r < t[2] + t[1]: return "2B"
		return "1B"
	return "OUT"
