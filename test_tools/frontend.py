#!/usr/bin/env python3
"""
Test frontend - simple console UI for testing conversation.
Sends input to backend and displays responses.
"""

import sys
import logging
import zmq
import time
import threading
from pathlib import Path

# Add parent directory to Python path so 'aist' module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)-7s] %(message)s'
)
log = logging.getLogger(__name__)

from aist.core.config_manager import config


class TestFrontend:
    def __init__(self):
        self.context = zmq.Context()
        
        # IPC Sockets
        self.test_input_socket = None
        self.test_output_socket = None
        
        self.running = True
        self.last_response = None
    
    def connect_to_backend(self):
        """Connect to test backend."""
        log.info("Connecting to test backend...")
        
        # Output socket: sends test messages to backend
        self.test_input_socket = self.context.socket(zmq.PUSH)
        self.test_input_socket.connect("tcp://127.0.0.1:15555")
        
        # Input socket: receives responses from backend
        self.test_output_socket = self.context.socket(zmq.SUB)
        self.test_output_socket.connect("tcp://127.0.0.1:15556")
        self.test_output_socket.subscribe(b"")  # Subscribe to all messages
        
        # Give backend time to connect
        time.sleep(0.5)
        log.info("✅ Connected to backend\n")
    
    def show_banner(self):
        """Show startup banner."""
        print("\n" + "=" * 70)
        print("🧪 AIST Conversation Tester - Frontend")
        print("=" * 70)
        print("\n⚙️  Configuration:")
        print(f"   STT Provider:    {config.get('models.stt.provider')}")
        print(f"   STT Model:       {config.get('models.stt.whisper_model_name')}")
        print(f"   Energy Thresh:   {config.get('audio.stt.energy_threshold')}")
        print(f"   Confidence:      {config.get('audio.stt.confidence_threshold')}")
        print(f"   TTS Provider:    {config.get('models.tts.provider')}")
        print(f"   LLM:             {config.get('models.llm.path').split('/')[-1]}")
        print("\nCommands:")
        print("   'help'     - Show help")
        print("   'settings' - Show configuration")
        print("   'clear'    - Clear screen")
        print("   'exit'     - Quit")
        print("\n" + "=" * 70 + "\n")
    
    def show_settings(self):
        """Show configuration."""
        print("\n" + "=" * 70)
        print("⚙️  CURRENT SETTINGS:")
        print("=" * 70)
        print(f"STT Provider:         {config.get('models.stt.provider')}")
        print(f"STT Model:            {config.get('models.stt.whisper_model_name')}")
        print(f"Energy Threshold:     {config.get('audio.stt.energy_threshold')}")
        print(f"Confidence Threshold: {config.get('audio.stt.confidence_threshold')}")
        print(f"TTS Provider:         {config.get('models.tts.provider')}")
        print(f"LLM GPU Layers:       {config.get('models.llm.gpu_layers')}")
        print("\n💡 To adjust: Edit config.yaml and restart backend\n")
        print("=" * 70 + "\n")
    
    def listen_responses(self):
        """Background thread to listen for responses."""
        while self.running:
            try:
                message = self.test_output_socket.recv_json(zmq.NOBLOCK)
                self.last_response = message
                
                # Display response
                user_input = message.get('user_input', '?')
                response = message.get('response')
                status = message.get('status', '?')
                
                print()
                print("─" * 70)
                print(f"👤 Input:     {user_input}")
                print(f"🤖 Response:  {response if response else '(no response)'}")
                print(f"📊 Status:    {status.upper()}")
                print("─" * 70)
                print()
                
            except zmq.Again:
                time.sleep(0.05)
            except Exception as e:
                if self.running:
                    log.debug(f"Listen error: {e}")
                time.sleep(0.1)
    
    def run(self):
        """Main input loop."""
        try:
            self.connect_to_backend()
            self.show_banner()
            
            # Start response listener thread
            listener = threading.Thread(target=self.listen_responses, daemon=True)
            listener.start()
            
            while True:
                try:
                    user_input = input("📝 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    if user_input.lower() == 'exit':
                        print("\n👋 Goodbye!")
                        self.running = False
                        break
                    elif user_input.lower() == 'help':
                        print("\nCommands:")
                        print("  settings - Show current config")
                        print("  clear    - Clear screen")
                        print("  exit     - Quit\n")
                        continue
                    elif user_input.lower() == 'settings':
                        self.show_settings()
                        continue
                    elif user_input.lower() == 'clear':
                        import os
                        os.system('cls' if sys.platform == 'win32' else 'clear')
                        self.show_banner()
                        continue
                    
                    # Send to backend
                    print("\n⏳ Waiting for response...")
                    self.test_input_socket.send_json({
                        'text': user_input
                    })
                    
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted")
                    self.running = False
                    break
                    
        except Exception as e:
            log.error(f"Frontend error: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        self.running = False
        if self.test_input_socket:
            self.test_input_socket.close()
        if self.test_output_socket:
            self.test_output_socket.close()
        if self.context:
            self.context.term()


if __name__ == "__main__":
    import threading
    frontend = TestFrontend()
    frontend.run()
