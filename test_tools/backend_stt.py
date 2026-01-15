#!/usr/bin/env python3
"""
Test backend with STT support - handles voice input, LLM, TTS processing.
With separate logging system - logs to data/logs/test_backend.log
"""

import sys
import logging
import json
import zmq
import threading
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Add parent directory to Python path so 'aist' module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup file logging FIRST
def setup_logging(log_file="data/logs/test_backend.log"):
    """Setup both file and console logging."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # File handler - rotating
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '[%(asctime)s] [%(levelname)-7s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('[%(levelname)-7s] %(name)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

log = setup_logging()

log.info("=" * 70)
log.info("TEST BACKEND STT Starting...")
log.info("=" * 70)
log.info(f"Command: {' '.join(sys.argv)}")
log.info(f"Log file: data/logs/test_backend.log")
log.info("")

from aist.core.config_manager import config
from aist.core.llm import initialize_llm, process_with_llm
from aist.core.tts import initialize_tts_engine, subscribe_to_events as tts_subscribe
from aist.core.stt import initialize_stt_engine
from aist.core.events import bus
from aist.core.ipc.event_bus import EventBroadcaster


class TestBackendWithSTT:
    def __init__(self, use_voice=False):
        self.use_voice = use_voice
        self.llm = None
        self.tts_engine = None
        self.stt_engine = None
        self.conversation_history = []
        self.context = zmq.Context()
        self.event_broadcaster = EventBroadcaster()
        
        # IPC Sockets
        self.test_input_socket = None
        self.test_output_socket = None
        self.is_running = True
        
        log.info(f"✅ Backend initialized - Voice mode: {use_voice}")
        
    def setup_ipc(self):
        """Setup IPC communication."""
        log.info("Setting up IPC...")
        
        try:
            # Input socket: receives test messages from frontend
            self.test_input_socket = self.context.socket(zmq.PULL)
            self.test_input_socket.bind("tcp://127.0.0.1:15555")
            log.info("✅ Test input listener on tcp://127.0.0.1:15555")
            
            # Output socket: broadcasts responses to frontend
            self.test_output_socket = self.context.socket(zmq.PUB)
            self.test_output_socket.bind("tcp://127.0.0.1:15556")
            log.info("✅ Test output broadcaster on tcp://127.0.0.1:15556\n")
        except Exception as e:
            log.error(f"❌ IPC setup failed: {e}", exc_info=True)
            raise
    
    def setup_components(self):
        """Initialize LLM and TTS. STT loads in background (non-blocking)."""
        log.info("=" * 70)
        log.info("COMPONENT SETUP")
        log.info("=" * 70)
        
        log.info("📋 Configuration:")
        log.info(f"  LLM: {config.get('models.llm.path')}")
        log.info(f"  TTS Provider: {config.get('models.tts.provider')}")
        log.info(f"  STT Provider: {config.get('models.stt.provider')}")
        log.info(f"  Voice Mode: {self.use_voice}\n")
        
        # Initialize LLM
        log.info("🤖 Loading LLM...")
        try:
            self.llm = initialize_llm(self.event_broadcaster)
            if not self.llm:
                log.error("❌ LLM initialization returned None")
                return False
            log.info("✅ LLM loaded\n")
        except Exception as e:
            log.error(f"❌ LLM failed: {e}", exc_info=True)
            return False
        
        # Initialize TTS
        log.info("🔊 Loading TTS...")
        try:
            self.tts_engine = initialize_tts_engine()
            # IMPORTANT: Subscribe to TTS events
            tts_subscribe()
            log.info("✅ TTS loaded\n")
        except Exception as e:
            log.warning(f"⚠️  TTS failed (non-critical): {e}\n")
            self.tts_engine = None
        
        # Initialize STT in background (non-blocking) if voice mode
        if self.use_voice:
            log.info("🎤 Starting STT initialization in background (30-second timeout)...")
            stt_thread = threading.Thread(
                target=self._init_stt_background,
                daemon=True
            )
            stt_thread.start()
        
        return True
    
    def _init_stt_background(self):
        """Initialize STT in background - non-blocking."""
        try:
            log.info("  [STT Thread] Starting...")
            stt_ready = threading.Event()
            self.stt_engine = initialize_stt_engine(self, stt_ready)
            log.info("  [STT Thread] ✅ Ready")
        except Exception as e:
            log.error(f"  [STT Thread] ❌ Error: {e}", exc_info=True)
            self.use_voice = False
    
    def process_message(self, user_input):
        """Process input and return response."""
        log.info(f"Processing: '{user_input}'")
        
        try:
            # Get LLM response
            response = process_with_llm(
                llm=self.llm,
                command=user_input,
                conversation_history=[(msg['role'], msg['content']) for msg in self.conversation_history],
                relevant_facts=[]
            )
            
            if response:
                # Add to history
                self.conversation_history.append({
                    'role': 'user',
                    'content': user_input
                })
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': response
                })
                
                # Keep history reasonable
                max_history = config.get('assistant.conversation_history_length', 5) * 2
                if len(self.conversation_history) > max_history:
                    self.conversation_history = self.conversation_history[-max_history:]
                
                log.info(f"✅ Response: '{response[:80]}'...")
                return response
            else:
                log.warning("⚠️  LLM returned empty")
                return None
                
        except Exception as e:
            log.error(f"❌ Processing failed: {e}", exc_info=True)
            return None
    
    def speak_response(self, response):
        """Speak via TTS."""
        if not self.tts_engine:
            log.debug("TTS not available - skipping speech")
            return
        
        try:
            log.info(f"🎙️  Speaking: '{response[:60]}'...")
            bus.sendMessage('tts.speak', text=response)
            log.debug("✅ TTS message sent")
        except Exception as e:
            log.error(f"❌ TTS error: {e}", exc_info=True)
    
    def process_and_respond(self, user_input):
        """Process input and broadcast response."""
        try:
            response = self.process_message(user_input)
            
            if response:
                result = {
                    'user_input': user_input,
                    'response': response,
                    'status': 'success'
                }
                self.test_output_socket.send_json(result)
                log.info("📤 Response sent to frontend")
                
                # Speak if enabled
                if config.get('models.tts.provider'):
                    self.speak_response(response)
            else:
                result = {
                    'user_input': user_input,
                    'response': None,
                    'status': 'failed'
                }
                self.test_output_socket.send_json(result)
                log.warning("📤 Failed status sent")
                
        except Exception as e:
            log.error(f"❌ Error: {e}", exc_info=True)
            try:
                result = {
                    'user_input': user_input,
                    'response': None,
                    'status': 'error',
                    'error': str(e)
                }
                self.test_output_socket.send_json(result)
            except:
                pass
    
    def listen_from_stt(self):
        """Listen for STT transcriptions."""
        log.info("🎤 Voice input listener started")
        
        def on_transcribed(text):
            """Callback when speech is transcribed."""
            if text and self.is_running:
                log.info(f"🎤 Heard: '{text}'")
                self.process_and_respond(text)
        
        try:
            bus.subscribe(on_transcribed, 'stt.transcribed')
            log.info("✅ Subscribed to speech events\n")
            
            # Keep listener alive
            while self.is_running:
                time.sleep(1)
        except Exception as e:
            log.error(f"❌ STT listener error: {e}", exc_info=True)
    
    def listen_loop(self):
        """Main listening loop for text input."""
        log.info("=" * 70)
        log.info("🚀 READY - Listening for input")
        log.info("=" * 70 + "\n")
        
        # Start voice listener if voice mode
        if self.use_voice:
            log.info("Starting voice listener thread...")
            voice_thread = threading.Thread(target=self.listen_from_stt, daemon=True)
            voice_thread.start()
            time.sleep(0.5)  # Let it start
        
        while self.is_running:
            try:
                # Non-blocking receive
                message = self.test_input_socket.recv_json(zmq.NOBLOCK)
                
            except zmq.Again:
                time.sleep(0.1)
                continue
            except KeyboardInterrupt:
                log.info("Keyboard interrupt")
                break
            except Exception as e:
                log.error(f"Receive error: {e}")
                continue
            
            try:
                user_input = message.get('text', '').strip()
                if not user_input:
                    continue
                
                log.info(f"📥 Text input: '{user_input}'")
                self.process_and_respond(user_input)
                
            except Exception as e:
                log.error(f"Error processing: {e}", exc_info=True)
    
    def run(self):
        """Start backend."""
        try:
            self.setup_ipc()
            if self.setup_components():
                self.listen_loop()
        except KeyboardInterrupt:
            log.info("\n👋 Keyboard interrupt")
        except Exception as e:
            log.error(f"❌ Fatal: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        log.info("Cleaning up...")
        self.is_running = False
        
        try:
            if self.test_input_socket:
                self.test_input_socket.close()
            if self.test_output_socket:
                self.test_output_socket.close()
            if self.event_broadcaster:
                self.event_broadcaster.stop()
            if self.context:
                self.context.term()
        except:
            pass
        
        log.info("✅ Cleanup complete")
        log.info("=" * 70 + "\n")


if __name__ == "__main__":
    use_voice = "--voice" in sys.argv
    backend = TestBackendWithSTT(use_voice=use_voice)
    backend.run()
