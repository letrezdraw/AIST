# test_tools/send_text_command.py
import zmq
import sys

def send_command(text: str):
    """Sends a text command to the AIST assistant."""
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    # Port 5557 is the default text command port for the main application
    socket.connect("tcp://localhost:5557") 
    
    print(f"Sending command: '{text}'")
    socket.send_string(text)
    
    socket.close()
    context.term()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command_text = " ".join(sys.argv[1:])
        send_command(command_text)
    else:
        print("Usage: python test_tools/send_text_command.py <your command>")
        print("Example: python test_tools/send_text_command.py what time is it")
