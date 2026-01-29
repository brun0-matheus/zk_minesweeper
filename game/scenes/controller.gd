extends Control

var GRID_SIZE = 10
var GAME_INITIALIZED = false
var LAST_PRESS = []

var GAME_STATE = ''

var BTN_PATH = "/root/Control/MarginContainer/PanelContainer/MarginContainer/HBoxContainer/MarginContainer/GridContainer/Button"

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
			


func _hpost(url: String, body: Dictionary) -> Error:
	var headers = [
		"Content-Type: application/json",
	]
	
	print("sent POST to ", url, body)
	
	return %HTTPRequest.request("http://localhost:5000/" + url, headers, HTTPClient.METHOD_POST, JSON.stringify(body))


func _hput(url: String, body: Dictionary) -> Error:
	var headers = [
		"Content-Type: application/json",
	]
	
	print("sent PUT to ", url, body)
	
	return %HTTPRequest.request("http://localhost:5000/" + url, headers, HTTPClient.METHOD_PUT, JSON.stringify(body))


func _hget(url: String) -> Error:
	var headers = [
		"Content-Type: application/json",
	]

	print("sent GET to ", url)

	return %HTTPRequest.request("http://localhost:5000/" + url, headers, HTTPClient.METHOD_GET, "")

func _on_start_pressed():
	GAME_INITIALIZED = false
	%TxtConsole.clear()
	_hpost("api/setup", {})


func _on_btn_pressed(coords):
	LAST_PRESS = coords
	if GAME_INITIALIZED == false:
		_hpost("api/init", {"c_x": coords[0], "c_y": coords[1]})
		return

	else:
		_hpost("api/dig", {"x": coords[0], "y": coords[1]})
	

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
			var btn: Button = get_node_or_null(BTN_PATH + str(coords[0]) + str(coords[1]))
			var btn_flag = load("uid://22knxqinbccq")
			var btn_base = load("uid://c6ky12hstygjc")
			
			var style = btn.get_theme_stylebox("normal")
			if style == btn_flag:
				btn.add_theme_stylebox_override("normal", btn_base)
				btn.add_theme_stylebox_override("hover", btn_base)
			else:
				btn.add_theme_stylebox_override("normal", load("uid://22knxqinbccq"))
				btn.add_theme_stylebox_override("hover", load("uid://22knxqinbccq"))


func _append_console(txt: String):
	var lines = %TxtConsole.get_line_count()
	var idx = lines - 1
	%TxtConsole.insert_line_at(idx, txt)
	%TxtConsole.set_line_as_first_visible(idx)

func _on_request_completed(result, response_code, headers, body):
	print(headers)
	var json = JSON.parse_string(body.get_string_from_utf8())
	print(json)
	
	if "game_state" in json:
		var gs = json['game_state']
		match gs:
			"setup":
				print("game is setup")
				_append_console("[SERVER] setup game")
			"init":
				_append_console("[SERVER] initialized game")
				await get_tree().create_timer(.25).timeout
				_append_console("[CLIENT] requested challenge for game creation")
				await get_tree().create_timer(.25).timeout
				_hget("api/create_game")
			"challenge_create_game":
				var challenge = json['data']['challenge']
				_append_console("[CLIENT] generated challenge: ")
				_append_console(challenge)
				await get_tree().create_timer(.25).timeout
				_append_console("[CLIENT] requesting server response")
				await get_tree().create_timer(.25).timeout
				_hpost("api/create_game", {"challenge": challenge})
			"challenge_create_game_reply":
				var challenge = json['data']['challenge']
				var response = json['data']['response']
				_append_console("[SERVER] received response from server: ")
				_append_console(response)
				await get_tree().create_timer(.125).timeout
				_hput("api/create_game", {"challenge": challenge, "response": response})
			"challenge_create_game_verified":
				var verified = bool(json['data']['verified'])
				var mine_count = int(json['data']['mine_count'])
				
				_append_console("[CLIENT] verified game settings. mine count: " + str(mine_count))
				_append_console("[CLIENT] requesting game permutation from server")
				
				_hpost("api/permute", {})
			"ready":
				var num_commits = int(json['data']['permutation_length'])
				_append_console("[CLIENT] received number of commitments: " + str(num_commits))
				GAME_INITIALIZED = true
			"dig_mine":
				var is_mine = bool(json['data']['mine'])
				var x = int(json['data']['x'])
				var y = int(json['data']['y'])
				var secret = json['data']['secret']
				
				_append_console("[SERVER] revealed commitment at (%d,%d), found mine" % [x, y])
				await get_tree().create_timer(.125).timeout
				_append_console("[CLIENT] verifying info from server")
				await get_tree().create_timer(.125).timeout
				
				_hput("api/dig", {"secret": secret, "is_mine": is_mine, "x": x, "y": y})
			"dig_mine_verified":
				var verified = bool(json['data']['verified'])
				var x = int(json['data']['x'])
				var y = int(json['data']['y'])
				
				var btn: Button = get_node_or_null(BTN_PATH + str(x) + str(y))
				
				_append_console("[CLIENT] verified information")
				
				var btn_mine = load("uid://cr55skwv5xqgr")
				
				btn.add_theme_stylebox_override("normal", btn_mine)
				btn.add_theme_stylebox_override("pressed", btn_mine)
				btn.add_theme_stylebox_override("disabled", btn_mine)
				btn.add_theme_stylebox_override("hover", btn_mine)
			"dig_challenge":
				var x = int(json['data']['x'])
				var y = int(json['data']['y'])
				var cnt = int(json['data']['mine_count'])
				var challenge = json['data']['challenge']
				
				_append_console("[SERVER] cell at (%d,%d) has %d neighboring mines" % [x, y, cnt])
				await get_tree().create_timer(.125).timeout
				_append_console("[CLIENT] requesting response from server with challenge")
				_append_console(challenge)
				
				await get_tree().create_timer(.125).timeout
				
				_hput("api/dig", {"challenge": challenge, "is_mine": false, "x": x, "y": y})
			"dig_challenge_reply":
				var challenge = json['data']['challenge']
				var response = json['data']['response']
				
				_append_console("[SERVER] response for client challenge is")
				_append_console(response)
				await get_tree().create_timer(.125).timeout
				_append_console("[CLIENT] verifying server response")
				
				await get_tree().create_timer(.125).timeout
				
				_hpost("api/verify_dig", {"challenge": challenge, "response": response})
			"dig_challenge_verified":
				var verified = bool(json['data']['verified'])
				var x = int(json['data']['x'])
				var y = int(json['data']['y'])
				var cnt = int(json['data']['mine_count'])
				
				_append_console("[CLIENT] verified response from server")
				
				var btn: Button = get_node_or_null(BTN_PATH + str(x) + str(y))
				_update_btn(btn, str(cnt))
			_:
				pass
	
	#if "data" in json:
	#	if "mine_count" in json['data']:
	#		var btn: Button = get_node_or_null("/root/Control/MarginContainer/PanelContainer/MarginContainer/GridContainer/Button" + str(LAST_PRESS[0]) + str(LAST_PRESS[1]))
	#		_update_btn(btn, str(int(json['data']['mine_count'])))
	#	elif "is_mine" in json['data']:
	#		var btn: Button = get_node_or_null("/root/Control/MarginContainer/PanelContainer/MarginContainer/GridContainer/Button" + str(LAST_PRESS[0]) + str(LAST_PRESS[1]))
	#		_update_btn(btn, "B")
			

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
