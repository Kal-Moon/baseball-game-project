## 2단계 확인용 스크린샷 (화면이 있어야 함: 클라우드에서는 xvfb-run).
## 실행: xvfb-run -s "-screen 0 1280x720x24" godot --path prototype/batting --script res://tests/screenshot.gd -- <저장 폴더>
## ① 공이 날아오는 중 ② 투구 뒤 표시 ③ 구종 11개 회전 그림 모음 ④ 배트 스윙 + 맞은 순간 번쩍임 ⑤ 인플레이 결과(4단계) ⑥ 조절판
extends SceneTree

const AtBat := preload("res://ui/at_bat.gd")
const PitchTypes := preload("res://core/pitch_types.gd")

var out := "user://"
var scene: Node2D
var sheet_node: Node2D
var step := 0
var frames := 0


## 구종별 공 길 (변화 크기 2배, 같은 도착 위치). 점 = 같은 시간 간격 (빽빽할수록 느림)
class PathSheet extends Node2D:
	func _draw() -> void:
		draw_rect(Rect2(0, 0, 1280, 720), Color("#2f6b3a"))
		var font := ThemeDB.fallback_font
		var Flight = load("res://core/pitch_flight.gd")
		var names := ["포심", "커브", "슬라이더", "스위퍼", "스플리터", "체인지업"]
		for i in names.size():
			var f = Flight.new()
			f.setup(names[i], {"x": 0.0, "y": -0.2, "kind": "normal"}, 650.0, 0, 50.0, 50.0, 0.0, 1.0, 2.0)
			# 구종마다 칸 하나 (화면을 0.55배로 줄여서 6칸)
			var off := Vector2(-170 + (i % 3) * 420, -40 + (i / 3) * 340)
			draw_set_transform(off, 0.0, Vector2(0.55, 0.55))
			var tl := AtBat.zone_to_screen(Vector2(-1, 1))
			draw_rect(Rect2(tl, AtBat.ZONE_H * 2.0), Color(1, 1, 1, 0.8), false, 3.0)
			var steps := int(f.travel_ms / 33.0)
			for k in steps + 1:
				var pp := float(k) / steps
				var q := AtBat.persp(pp)
				# 회색 = 처음 향하던 곳으로 곧게 갔다면
				draw_circle(AtBat.RELEASE.lerp(AtBat.zone_to_screen(f.target - f.move), q), 3.0, Color(1, 1, 1, 0.3))
				draw_circle(f.screen_pos(pp, AtBat.RELEASE, AtBat.zone_to_screen, q), 3.0 + 8.0 * q, Color("#ffe066"))
			draw_string(font, Vector2(560, 650), "%s %dkm/h %dms" % [names[i], f.kmh, roundi(f.travel_ms)], HORIZONTAL_ALIGNMENT_LEFT, -1, 40, Color.WHITE)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		draw_string(font, Vector2(0, 30), "구종별 공 길 (노랑 = 실제, 회색 = 휘지 않았다면, 변화 크기 2배, 점 사이 1/30초)", HORIZONTAL_ALIGNMENT_CENTER, 1280, 22, Color.WHITE)


class SpinSheet extends Node2D:
	var t := 0.0
	func _draw() -> void:
		draw_rect(Rect2(0, 0, 1280, 720), Color("#2f6b3a"))
		var font := ThemeDB.fallback_font
		for i in PitchTypes.NAMES.size():
			var n: String = PitchTypes.NAMES[i]
			var pos := Vector2(140 + (i % 6) * 200, 200 + (i / 6) * 300)
			draw_circle(pos, 60, Color("#f4f1e8"))
			AtBat.draw_spin(self, pos, 60, n, t)
			draw_string(font, pos + Vector2(-90, 100), n, HORIZONTAL_ALIGNMENT_CENTER, 180, 26, Color.WHITE)
		draw_string(font, Vector2(0, 50), "구종별 회전 그림 (공 크기를 키워서 본 것, 한 순간)", HORIZONTAL_ALIGNMENT_CENTER, 1280, 26, Color.WHITE)


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out = args[0]
	scene = load("res://ui/at_bat.tscn").instantiate()
	root.add_child(scene)


func _process(_dt: float) -> bool:
	frames += 1
	if frames < 5:
		return false
	match step:
		0:
			scene.fake_now = 0
			scene.throw_pitch("커브", {"x": 0.4, "y": -0.6, "kind": "normal"})
			scene.fake_now = int(scene.flight.release_usec + (scene.flight.arrive_usec - scene.flight.release_usec) * 0.82)
			scene.queue_redraw()
		1:
			_save("2-1_flight.png")
			scene.fake_now = scene.flight.arrive_usec - 18_000
			var down := InputEventScreenTouch.new(); down.pressed = true; down.position = Vector2(640, 500)
			scene._input(down)
			var up := InputEventScreenTouch.new(); up.pressed = false; up.position = Vector2(500, 505)
			scene._input(up)
			scene.contact = "strong"                 # 반응 그림 확인용으로 강한 타구로 고정
			scene.flash_start = scene.flight.arrive_usec
			scene.fake_now = scene.flight.arrive_usec + 60_000
			scene.queue_redraw()
		2:
			_save("2-4_swing_contact.png")
			scene.fake_now = scene.flight.arrive_usec + 250_000
			scene.tick()
			scene.queue_redraw()
		3:
			_save("2-2_after_pitch.png")
			scene.queue_free()
			sheet_node = SpinSheet.new()
			sheet_node.t = 0.03
			root.add_child(sheet_node)
		4:
			_save("2-3_spin_sheet.png")
			sheet_node.queue_free()
			scene = load("res://ui/at_bat.tscn").instantiate()
			root.add_child(scene)
			scene.fake_now = 0
			scene._ready()
			for k in scene.tally: scene.tally[k] = 0
			scene.tally.merge({"PA": 12, "AB": 10, "H": 3, "2B": 1, "HR": 1, "K": 2, "BB": 2}, true)
			scene.pitcher.pitches = ["포심", "슬라이더", "체인지업"]
			scene.throw_pitch("슬라이더", {"x": 0.2, "y": 0.1, "kind": "normal"})
			scene.fake_now = scene.flight.arrive_usec - 5_000
			var d := InputEventScreenTouch.new(); d.pressed = true; d.position = Vector2(640, 500)
			scene._input(d)
			scene.swing = "당겨치기"; scene.level = 0; scene.swing_result = "strong"; scene.contact = "strong"
			scene.model.rng.seed = 3
			scene.fake_now = scene.flight.arrive_usec + 250_000
			scene.tick()
			scene.fake_now = scene.show_start + 900_000
			scene.queue_redraw()
		5:
			_save("4-1_in_play.png")
			scene.panel_open = true
			scene.queue_redraw()
		6:
			_save("4-2_panel.png")
			scene.queue_free()
			root.add_child(PathSheet.new())
		7:
			_save("4-3_pitch_paths.png")
			quit()
	step += 1
	frames = 0
	return false


func _save(name: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name))
	print("저장: ", out.path_join(name))
