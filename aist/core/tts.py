# core/tts.py - Pluggable Text-to-Speech Engine Manager
import logging
import threading
import importlib
from aist.core.config_manager import config
from aist.core.events import bus, TTS_SPEAK
from aist.core.ipc.protocol import INIT_STATUS_UPDATE # New import

log = logging.getLogger(__name__)

# Global instance of the TTS provider
tts_provider = None

def initialize_tts_engine(event_broadcaster):
    """
    Initializes the configured TTS provider.
    This should be called once at application startup.
    Returns the provider instance on success, or None on failure.
    """
    global tts_provider
    provider_name = config.get('models.tts.provider', 'piper')
    log.info(f"Initializing TTS engine with provider: '{provider_name}'")

    try:
        provider_module = importlib.import_module(f"aist.tts_providers.{provider_name}_provider")
        ProviderClass = getattr(provider_module, f"{provider_name.capitalize()}Provider")
        tts_provider = ProviderClass()
        log.info(f"TTS provider '{provider_name}' initialized.")
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "tts", "status": "initialized"}) # Send update
    except (ImportError, AttributeError) as e:
        log.fatal(f"Failed to load TTS provider '{provider_name}'. Please check your configuration.")
        log.error(e, exc_info=True)
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "tts", "status": "failed", "error": str(e)}) # Send error update
    except Exception as e:
        log.fatal(f"An unexpected error occurred while initializing the TTS provider '{provider_name}'.")
        log.error(e, exc_info=True)
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "tts", "status": "failed", "error": str(e)}) # Send error update
    return tts_provider

def _handle_speak_request(text: str):
    """
    Handles a speak request from the event bus.
    Runs the actual speaking in a separate thread to avoid blocking the bus.
    """
    if not text or not tts_provider:
        return
    threading.Thread(target=tts_provider.speak, args=(text,), daemon=True).start()

def subscribe_to_events():
    """Subscribes the TTS engine to the event bus."""
    if tts_provider:
        bus.subscribe(_handle_speak_request, TTS_SPEAK)
        log.info("TTS engine is listening for 'tts.speak' events.")
    else:
        log.warning("No TTS provider loaded. TTS will be silent.")