extends Control

var GRID_SIZE = 10
var GAME_INITIALIZED = false
var LAST_PRESS = []

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	
	var btn_base = load("uid://c6ky12hstygjc")
	var btn_pressed = load("uid://q2ia27ssqccs")
	
	%BtnStart.pressed.connect(_on_start_pressed)
	%HTTPRequest.request_completed.connect(_on_request_completed)
	
	var container = $%GridContainer
	
	for i in range(GRID_SIZE):
		for j in range(GRID_SIZE):
			var btn = Button.new()
			btn.add_theme_stylebox_override("normal", btn_base)
			btn.add_theme_stylebox_override("pressed", btn_pressed)
			btn.add_theme_stylebox_override("disabled", btn_pressed)
			btn.add_theme_stylebox_override("hover", btn_base)
			btn.add_theme_font_size_override("font_size", 18)
			
			btn.pressed.connect(_on_btn_pressed.bind([i, j]))
			btn.gui_input.connect(_on_btn_input.bind([i, j]))
			
			btn.custom_minimum_size = Vector2(32, 32)
			btn.toggle_mode = true
			btn.name = "Button" + str(i) + str(j)
			btn.unique_name_in_owner = true
			
			container.add_child(btn)
			print(btn.get_path())
			


func _post(url: String, body: String) -> Error:
	var headers = [
		"Content-Type: application/json",
	]
	
	return %HTTPRequest.request(url, headers, HTTPClient.METHOD_POST, body)

func _on_start_pressed():
	print("Initializing game")
	
	_post("http://localhost:5000/api/setup", JSON.stringify({}))


func _on_btn_pressed(coords):
	LAST_PRESS = coords
	if GAME_INITIALIZED == false:
		_post("http://localhost:5000/api/init", JSON.stringify({"c_x": coords[0], "c_y": coords[1]}))
		return

	else:
		_post("http://localhost:5000/api/dig", JSON.stringify({"x": coords[0], "y": coords[1]}))
	

func _get_color_from_mine_count(count: String) -> Color:
	print("count is ", count)
	match count:
		"1":
			return Color("#0101f1")
		"2":
			return Color("#377c20")
		"3":
			return Color("#e83325")
		"4":
			return Color("#01007c")
		"5":
			return Color("#75150d")
		"6":
			return Color("#387e7e")
		"7":
			return Color("#000")
		"8":
			return Color("#808080")
		_:
			return Color(0.875, 0.875, 0.875, 1) 
			
		

func _update_btn(button: Button, text: String):
	if text == '0':
		text = ""
	button.text = text
	var color = _get_color_from_mine_count(text)
	button.add_theme_color_override("font_color", color)
	button.add_theme_color_override("font_disabled_color", color)
	button.add_theme_color_override("font_pressed_color", color)
	button.disabled = true


func _on_btn_input(event, coords):
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			var btn: Button = get_node_or_null("/root/Control/MarginContainer/PanelContainer/MarginContainer/GridContainer/Button" + str(coords[0]) + str(coords[1]))
			btn.add_theme_stylebox_override("normal", load("uid://22knxqinbccq"))
			btn.add_theme_stylebox_override("hover", load("uid://22knxqinbccq"))


func _on_request_completed(result, response_code, headers, body):
	print(headers)
	var json = JSON.parse_string(body.get_string_from_utf8())
	print(json)
	
	if "game_state" in json:
		if json["game_state"] == "setup":
			GAME_INITIALIZED = false
		if json["game_state"] == "init":
			GAME_INITIALIZED = true
	
	if "data" in json:
		if "mine_count" in json['data']:
			var btn: Button = get_node_or_null("/root/Control/MarginContainer/PanelContainer/MarginContainer/GridContainer/Button" + str(LAST_PRESS[0]) + str(LAST_PRESS[1]))
			_update_btn(btn, str(int(json['data']['mine_count'])))
		elif "is_mine" in json['data']:
			var btn: Button = get_node_or_null("/root/Control/MarginContainer/PanelContainer/MarginContainer/GridContainer/Button" + str(LAST_PRESS[0]) + str(LAST_PRESS[1]))
			_update_btn(btn, "B")
			

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
