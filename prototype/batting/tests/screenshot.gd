## 2단계 확인용 스크린샷 (화면이 있어야 함: 클라우드에서는 xvfb-run).
## 실행: xvfb-run -s "-screen 0 1280x720x24" godot --path prototype/batting --script res://tests/screenshot.gd -- <저장 폴더>
## ① 공이 날아오는 중 ② 투구 뒤 표시 ③ 구종 11개 회전 그림 모음
extends SceneTree

const AtBat := preload("res://ui/at_bat.gd")
const PitchTypes := preload("res://core/pitch_types.gd")

var out := "user://"
var scene: Node2D
var step := 0
var frames := 0


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
			scene.fake_now = scene.flight.arrive_usec + 250_000
			scene.tick()
			scene.queue_redraw()
		2:
			_save("2-2_after_pitch.png")
			scene.queue_free()
			var sheet := SpinSheet.new()
			sheet.t = 0.03
			root.add_child(sheet)
		3:
			_save("2-3_spin_sheet.png")
			quit()
	step += 1
	frames = 0
	return false


func _save(name: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name))
	print("저장: ", out.path_join(name))
