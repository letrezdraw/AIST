# core/stt.py - Pluggable Speech-to-Text Engine Manager

import logging
import threading
import importlib
from aist.core.log_setup import console_log
from aist.core.config_manager import config

log = logging.getLogger(__name__)

def initialize_stt_engine(app_state, stt_ready_event: threading.Event):
    """
    Initializes the configured STT provider and starts it in a background thread.
    """
    provider_name = config.get('models.stt.provider', 'vosk')
    console_log(f"Initializing STT engine with provider: '{provider_name}'")

    try:
        # Dynamically import the provider module
        provider_module = importlib.import_module(f"aist.stt_providers.{provider_name}_provider")
        # The class name is expected to be PascalCase, e.g., 'vosk' -> 'VoskProvider'
        ProviderClass = getattr(provider_module, f"{provider_name.capitalize()}Provider")
        
        provider_instance = ProviderClass(app_state, stt_ready_event)
        
        # Start the provider's listening loop in a background thread
        threading.Thread(target=provider_instance.run, daemon=True).start()

    except (ImportError, AttributeError) as e:
        log.fatal(f"Failed to load STT provider '{provider_name}'. Please check your configuration and ensure the provider file exists.")
        log.error(e, exc_info=True)
    except Exception as e:
        log.fatal(f"An unexpected error occurred while initializing the STT provider '{provider_name}'.")
        log.error(e, exc_info=True)