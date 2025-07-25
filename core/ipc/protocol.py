# core/ipc/protocol.py

# Defines the communication protocol constants and message formats.

# Server address
HOST = '127.0.0.1' # Localhost
PORT = 65432       # Port to listen on

# Message Types
MSG_CMD = "command"
MSG_SPEAK = "speak"
MSG_CONFIRM = "confirm"
MSG_CONFIRM_RESPONSE = "confirm_response"