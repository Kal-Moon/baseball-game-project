## 1단계 확인: 화면 없이 유저 세 단계로 타석을 돌려 simulation/direct_play_sim.py 결과와 비교.
## 실행: godot --headless --path prototype/batting --script res://tests/sim_test.gd -- [타석 수] [능력치 이름=값 ...]
extends SceneTree

const Model := preload("res://core/batting_model.gd")
const Params := preload("res://core/params.gd")


func plate_appearance(m, user: Dictionary) -> String:
	var balls := 0; var strikes := 0
	while true:
		var p: Dictionary = m.pitch_location(balls, strikes)
		var zone: bool = Model.in_zone(p["x"], p["y"])
		var p_sw: float
		if zone:
			p_sw = user["zone_swing"]
		else:
			p_sw = user["chase"] * (1.0 - Params.EYE["chase"] * m.slow) * (0.7 if absf(p["x"]) > 1.6 or absf(p["y"]) > 1.6 else 1.0)
		if strikes == 2:
			p_sw = minf(0.95, p_sw + (0.15 if zone else 0.05))
		if m.rng.randf() < p_sw:
			var g: int = m.pick(user["timing"])
			var c: int = m.pick(user["compat"])
			var res: String = m.resolve_swing(g, zone, p["kind"], c, true)[0]
			if res == "whiff":
				strikes += 1
			elif res == "foul":
				strikes = mini(2, strikes + 1)
			else:
				return m.ball_in_play(res)
			if strikes == 3: return "K"
			continue
		if m.is_hbp(p["x"]): return "HBP"
		if zone:
			strikes += 1
			if strikes == 3: return "K"
		else:
			balls += 1
			if balls == 4: return "BB"
	return ""


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var n := 100000
	var stats := {}
	for a in args:
		if a.contains("="):
			var kv := a.split("=")
			stats[kv[0]] = float(kv[1])
		elif a.is_valid_int():
			n = int(a)
	for uname in ["서툰", "보통", "잘함"]:
		var m = Model.new(1)
		m.set_stats(stats)
		var c := {}
		for i in n:
			var r := plate_appearance(m, Params.USERS[uname])
			c[r] = c.get(r, 0) + 1
		var hits: int = c.get("1B", 0) + c.get("2B", 0) + c.get("3B", 0) + c.get("HR", 0)
		var ab: int = n - c.get("BB", 0) - c.get("HBP", 0)
		var tb: int = c.get("1B", 0) + 2 * c.get("2B", 0) + 3 * c.get("3B", 0) + 4 * c.get("HR", 0)
		print("%s AVG %.3f OBP %.3f SLG %.3f K %.3f BB %.3f HBP %.4f HR %.4f" % [uname, float(hits) / ab,
			float(hits + c.get("BB", 0) + c.get("HBP", 0)) / n, float(tb) / ab, float(c.get("K", 0)) / n,
			float(c.get("BB", 0)) / n, float(c.get("HBP", 0)) / n, float(c.get("HR", 0)) / n])
	quit()
