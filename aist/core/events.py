# aist/core/events.py

from pubsub import pub

"""
This module defines the central message bus for the AIST application and the
standardized event topics used for communication between components.

By using a publish-subscribe model, we decouple all major components (STT, TTS,
LLM, GUI, Skills, etc.). They don't need to know about each other; they only
need to know about the events they are interested in.

The `bus` object is the central pubsub instance imported by all components.
"""

bus = pub.getDefaultPublisher()

# --- Event Topic Definitions ---
# These are the "channels" that components can publish to or subscribe from.
# Using constants for topic names helps prevent typos and makes the code
# easier to understand and maintain.

# Speech-to-Text (STT) Events
STT_TRANSCRIBED = 'stt.transcribed'  # Fired when text is successfully transcribed.
                                     # Data: {'text': str}

# Text-to-Speech (TTS) Events
TTS_SPEAK = 'tts.speak'              # Fired to request speech synthesis.
                                     # Data: {'text': str}
TTS_STARTED = 'tts.started'          # Fired when TTS playback begins.
TTS_FINISHED = 'tts.finished'        # Fired when TTS playback ends.

# Application State Events
STATE_CHANGED = 'state.changed'      # Fired when the assistant's state changes (DORMANT/LISTENING)
                                     # Data: {'state': str}

# Application Lifecycle Events
APP_STARTUP = 'app.startup'          # Fired when the application starts.
APP_SHUTDOWN = 'app.shutdown'        # Fired to signal a graceful shutdown.

# Command Dispatcher Events
COMMAND_PROCESSED = 'command.processed' # Fired after the backend processes a command.
                                        # Data: {'response': dict}