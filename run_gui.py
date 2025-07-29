# run_gui.py
import flet as ft
import logging
import zmq
import json
import threading

# --- Flet Theme Colors ---
COLOR_STATUS_MAP = {
    "INITIALIZING": ft.Colors.BLUE_GREY_400,
    "DORMANT": ft.Colors.AMBER_500,
    "LISTENING": ft.Colors.GREEN_400,
    "THINKING": ft.Colors.BLUE_400,
    "SPEAKING": ft.Colors.PURPLE_400,
}

def main(page: ft.Page):
    page.title = "AIST"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#141218" # A dark purple/grey
    page.padding = 0

    # --- UI Elements ---
    vad_dot = ft.Container(
        width=15,
        height=15,
        bgcolor=ft.Colors.GREY_800,
        border_radius=10,
        tooltip="Voice Activity",
        shadow=None,
        animate=ft.Animation(300, "ease")
    )
    conversation_view = ft.ListView(expand=True, spacing=10, auto_scroll=True, padding=20)
    status_text = ft.Text("INITIALIZING", size=12, weight=ft.FontWeight.BOLD, color=COLOR_STATUS_MAP["INITIALIZING"])
    text_input = ft.TextField(
        hint_text="Type a command...",
        expand=True,
        on_submit=lambda e: send_text_command(e),
        border_radius=20,
        border_color="transparent",
        bgcolor=ft.colors.with_opacity(0.05, ft.Colors.WHITE),
        height=40,
        content_padding=12
    )
    log_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)
    intent_name_text = ft.Text("Intent: -", size=11, color=ft.Colors.GREY_400, font_family="monospace")
    intent_params_text = ft.Text("Params: -", size=11, color=ft.Colors.GREY_400, font_family="monospace")
    status_indicators = {
        "Backend": ft.Text("Backend: Disconnected", color=ft.Colors.RED_400, size=11, font_family="monospace"),
        "Event Bus": ft.Text("Event Bus: Disconnected", color=ft.Colors.RED_400, size=11, font_family="monospace"),
        "STT": ft.Text("STT: Initializing", color=ft.Colors.BLUE_GREY_400, size=11, font_family="monospace"),
        "TTS": ft.Text("TTS: Initializing", color=ft.Colors.BLUE_GREY_400, size=11, font_family="monospace"),
    }
    side_panel = ft.Container(
        content=ft.Column([
            ft.Row(
                [
                    ft.Text("System Logs", weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: toggle_side_panel(e), tooltip="Close Panel")
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            ft.Divider(),
            log_view,
            ft.Divider(),
            ft.Text("Last Intent", weight=ft.FontWeight.BOLD),
            intent_name_text,
            intent_params_text,
            ft.Divider(),
            ft.Text("Component Status", weight=ft.FontWeight.BOLD),
            *status_indicators.values()
        ], expand=True),
        width=350,
        height=page.window_height,
        bgcolor=ft.Colors.with_opacity(0.97, "#18161c"),
        padding=15,
        visible=False,
        animate_position=ft.Animation(250, "easeOut"),
        right=0,
        top=0
    )

    # --- ZMQ Sockets & UI Event Handlers ---
    context = zmq.Context()
    text_command_socket = context.socket(zmq.PUSH)
    text_command_socket.connect("tcp://localhost:5557")

    def send_text_command(e):
        command_text = text_input.value.strip()
        if command_text:
            try:
                text_command_socket.send_string(command_text)
                text_input.value = ""
                page.update()
            except Exception as ex:
                logging.error(f"Failed to send text command: {ex}")

    def clear_conversation(e):
        try:
            text_command_socket.send_string("__AIST_CLEAR_CONVERSATION__")
            conversation_view.controls.clear()
            conversation_view.controls.append(ft.Text("Conversation cleared.", italic=True, color=ft.Colors.GREY_500))
            page.update()
        except Exception as ex:
            logging.error(f"Failed to send clear command: {ex}")

    def toggle_side_panel(e):
        side_panel.visible = not side_panel.visible
        page.update()

    # --- Layout Definition ---
    page.appbar = ft.AppBar(
        leading=vad_dot,
        leading_width=50,
        title=status_text,
        center_title=True,
        bgcolor=ft.colors.with_opacity(0.05, ft.Colors.WHITE),
        actions=[
            ft.IconButton(icon=ft.Icons.DELETE_SWEEP_OUTLINED, on_click=clear_conversation, tooltip="Clear Conversation"),
            ft.IconButton(icon=ft.Icons.MENU, on_click=toggle_side_panel, tooltip="View Logs & Status"),
        ]
    )
    main_content_column = ft.Column(
        [
            ft.Container(
                content=conversation_view,
                expand=True,
            ),
            ft.Divider(height=1),
            ft.Container(
                content=ft.Row(
                    [
                        text_input,
                        ft.IconButton(icon=ft.Icons.SEND_ROUNDED, on_click=send_text_command, tooltip="Send Command")
                    ],
                ),
                padding=ft.padding.only(left=15, right=15, bottom=10, top=5)
            )
        ],
        expand=True
    )

    page.add(
        ft.Stack(
            [
                main_content_column,
                side_panel
            ]
        )
    )

    # --- ZMQ Event Listener ---
    def event_listener():
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5556")
        socket.setsockopt(zmq.SUBSCRIBE, b'') # Subscribe to all topics

        log_socket = context.socket(zmq.SUB)
        log_socket.connect("tcp://localhost:5558")
        log_socket.setsockopt(zmq.SUBSCRIBE, b'')

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        poller.register(log_socket, zmq.POLLIN)

        logging.info("GUI event listener connected.")
        while True:
            try:
                socks = dict(poller.poll(1000))
                if socket in socks:
                    topic, payload_str = socket.recv_multipart()
                    topic = topic.decode('utf-8')
                    payload = json.loads(payload_str.decode('utf-8'))
                    handle_event(topic, payload)
                
                if log_socket in socks:
                    log_message = log_socket.recv_string()
                    handle_log_record(log_message)

            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM:
                    break # Context terminated, exit loop
                else:
                    logging.error(f"ZMQ Error: {e}")
            except Exception as e:
                logging.error(f"Error processing event: {e}")

    def handle_log_record(message: str):
        log_view.controls.append(ft.Text(message, size=10, font_family="monospace"))
        # Resilient fallback to update component status by parsing the log stream.
        # This ensures the GUI status is correct even if the initial ZMQ event is missed.
        if "component:status" in message:
            try:
                parts = message.split("'")
                if len(parts) >= 5:
                    name, status = parts[1], parts[3]
                    if name in status_indicators:
                        indicator = status_indicators[name]
                        indicator.value = f"{name}: {status}"
                        indicator.color = ft.Colors.GREEN_400 if status in ["Ready", "Connected", "Broadcasting"] else ft.Colors.RED_400
            except Exception:
                pass # Ignore parsing errors
        page.update()

    # --- UI Update Logic ---
    def handle_event(topic, payload):
        if topic == "state:changed":
            state = payload.get("state", "UNKNOWN").upper()
            status_text.value = state
            status_text.color = COLOR_STATUS_MAP.get(state, ft.Colors.WHITE)

            # Give a visual cue when the AI is thinking
            if state == "THINKING":
                vad_dot.bgcolor = ft.Colors.BLUE_400
                vad_dot.shadow = ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.BLUE_400, blur_style=ft.ShadowBlurStyle.NORMAL)
            elif vad_dot.bgcolor == ft.Colors.BLUE_400:
                # Revert to silence color if we were thinking before
                vad_dot.bgcolor = ft.Colors.GREY_800
                vad_dot.shadow = None
        
        elif topic == "vad:status":
            status = payload.get("status", "UNKNOWN")
            vad_dot.bgcolor = ft.Colors.GREEN_ACCENT_400 if status == "SPEECH" else ft.Colors.GREY_800
            vad_dot.shadow = ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.GREEN_ACCENT_400, blur_style=ft.ShadowBlurStyle.NORMAL) if status == "SPEECH" else None

        elif topic == "component:status":
            name = payload.get("name")
            status = payload.get("status")
            if name in status_indicators:
                indicator = status_indicators[name]
                indicator.value = f"{name}: {status}"
                indicator.color = ft.Colors.GREEN_400 if status in ["Ready", "Connected", "Broadcasting"] else ft.Colors.RED_400
                # Also update the main status text if a core component fails
                if status == "Failed":
                    status_text.value = f"{name} FAILED"
                    status_text.color = ft.Colors.RED_400

        elif topic == "stt:heard":
            text = payload.get("text")
            # Clear previous intent when a new command is heard
            intent_name_text.value = "Intent: -"
            intent_params_text.value = "Params: -"
            conversation_view.controls.append(ft.Text(f"You: {text}", italic=True, color=ft.Colors.GREY_500))

        elif topic == "tts:speak":
            text = payload.get("text")
            conversation_view.controls.append(ft.Text(f"AIST: {text}", weight=ft.FontWeight.BOLD))
        
        elif topic == "intent:matched":
            intent_name_text.value = f"Intent: {payload.get('name', 'N/A')}"
            params