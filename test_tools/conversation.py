#!/usr/bin/env python3
"""
Simple conversation testing program.
Tests STT, LLM, and TTS with live config updates.

Usage:
    python test_conversation.py              # Text input mode
    python test_conversation.py --voice      # Voice input mode (requires STT)
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to Python path so 'aist' module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)-7s] %(name)s - %(message)s'
)
log = logging.getLogger(__name__)

# Import AIST components
from aist.core.config_manager import config
from aist.core.llm import initialize_llm, process_with_llm
from aist.core.tts import initialize_tts_engine
from aist.core.stt import initialize_stt_engine
from aist.core.events import bus
from aist.core.audio import audio_manager


class ConversationTester:
    def __init__(self, use_voice=False):
        self.use_voice = use_voice
        self.conversation_history = []
        self.llm = None
        self.tts_engine = None
        self.stt_engine = None
        
    def setup(self):
        """Initialize all components."""
        log.info("=" * 60)
        log.info("AIST Conversation Tester - Setup")
        log.info("=" * 60)
        
        # Show config
        log.info("📋 Configuration:")
        log.info(f"  LLM: {config.get('models.llm.path')}")
        log.info(f"  LLM GPU Layers: {config.get('models.llm.gpu_layers')}")
        log.info(f"  TTS Provider: {config.get('models.tts.provider')}")
        log.info(f"  STT Provider: {config.get('models.stt.provider')}")
        log.info(f"  Energy Threshold: {config.get('audio.stt.energy_threshold')}")
        log.info("")
        
        # Initialize LLM
        log.info("🤖 Loading LLM...")
        self.llm = initialize_llm()
        if not self.llm:
            log.error("Failed to initialize LLM")
            return False
        log.info("✅ LLM ready")
        
        # Initialize TTS
        log.info("🔊 Loading TTS...")
        try:
            self.tts_engine = initialize_tts_engine()
            log.info("✅ TTS ready")
        except Exception as e:
            log.error(f"Failed to initialize TTS: {e}")
            self.tts_engine = None
        
        # Initialize STT if voice mode
        if self.use_voice:
            log.info("🎤 Loading STT...")
            try:
                self.stt_engine = initialize_stt_engine()
                log.info("✅ STT ready")
            except Exception as e:
                log.error(f"Failed to initialize STT: {e}")
                self.use_voice = False
        
        log.info("")
        return True
    
    def get_user_input(self):
        """Get input from user (text or voice)."""
        if self.use_voice:
            print("\n🎤 Listening... (speak now)")
            # Voice input would go here
            print("⚠️  Voice input not yet implemented in this test")
            text = input("📝 Type instead: ").strip()
        else:
            print("\n" + "=" * 60)
            text = input("📝 You: ").strip()
        
        return text
    
    def get_llm_response(self, user_input):
        """Get response from LLM."""
        log.info(f"🧠 Sending to LLM: '{user_input}'")
        
        try:
            response = process_with_llm(
                llm=self.llm,
                command=user_input,
                conversation_history=[(msg['role'], msg['content']) for msg in self.conversation_history],
                relevant_facts=[]
            )
            
            if response:
                log.info(f"✅ LLM Response: '{response}'")
                return response
            else:
                log.warning("⚠️  LLM returned empty response")
                return None
                
        except Exception as e:
            log.error(f"❌ LLM Error: {e}", exc_info=True)
            return None
    
    def speak_response(self, response):
        """Speak the response via TTS."""
        if not self.tts_engine:
            log.info(f"🔇 (TTS disabled) Would say: {response}")
            return
        
        try:
            log.info(f"🎙️  Speaking: '{response}'")
            # Trigger TTS via event
            bus.sendMessage('tts.speak', text=response)
            
            # Give TTS time to process
            import time
            time.sleep(len(response) / 10)  # Rough estimate
            
        except Exception as e:
            log.error(f"TTS Error: {e}")
    
    def show_settings(self):
        """Show current settings."""
        print("\n" + "=" * 60)
        print("⚙️  CURRENT SETTINGS:")
        print("=" * 60)
        print(f"STT Provider: {config.get('models.stt.provider')}")
        print(f"STT Model: {config.get('models.stt.whisper_model_name')}")
        print(f"Energy Threshold: {config.get('audio.stt.energy_threshold')}")
        print(f"Confidence Threshold: {config.get('audio.stt.confidence_threshold')}")
        print(f"TTS Provider: {config.get('models.tts.provider')}")
        print(f"LLM GPU Layers: {config.get('models.llm.gpu_layers')}")
        print("\n💡 Tip: Edit config.yaml and settings will update on next run!")
        print("=" * 60)
    
    def run(self):
        """Main conversation loop."""
        if not self.setup():
            return
        
        print("\n" + "=" * 60)
        print("🚀 AIST Conversation Tester Started")
        print("=" * 60)
        print("Commands:")
        print("  'help'     - Show help")
        print("  'settings' - Show current settings")
        print("  'history'  - Show conversation history")
        print("  'exit'     - Quit")
        print("=" * 60)
        
        while True:
            try:
                user_input = self.get_user_input()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() == 'exit':
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("  settings - Show config")
                    print("  history  - Show conversation")
                    print("  exit     - Quit\n")
                    continue
                elif user_input.lower() == 'settings':
                    self.show_settings()
                    continue
                elif user_input.lower() == 'history':
                    print("\n📜 Conversation History:")
                    for i, msg in enumerate(self.conversation_history, 1):
                        role = msg.get('role', '?').upper()
                        content = msg.get('content', '?')[:60]
                        print(f"  {i}. [{role}] {content}...")
                    print()
                    continue
                
                # Normal conversation
                print(f"\n👤 You: {user_input}")
                
                # Get LLM response
                response = self.get_llm_response(user_input)
                
                if response:
                    print(f"\n🤖 Assistant: {response}\n")
                    
                    # Add to history
                    self.conversation_history.append({
                        'role': 'user',
                        'content': user_input
                    })
                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                    
                    # Keep history size reasonable
                    max_history = config.get('assistant.conversation_history_length', 5) * 2
                    if len(self.conversation_history) > max_history:
                        self.conversation_history = self.conversation_history[-max_history:]
                    
                    # Optional: speak response
                    if config.get('models.tts.provider'):
                        try:
                            self.speak_response(response)
                        except Exception as e:
                            log.debug(f"TTS failed (non-critical): {e}")
                else:
                    print("\n❌ Failed to get response from LLM\n")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                log.error(f"Error in conversation loop: {e}", exc_info=True)
                print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    use_voice = "--voice" in sys.argv
    
    tester = ConversationTester(use_voice=use_voice)
    tester.run()
