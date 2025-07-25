# core/user_interaction.py - Handles direct user interaction like confirmations.

import tkinter as tk
from tkinter import messagebox
import threading
from core.tts import speak

def ask_for_confirmation(prompt_text: str) -> bool:
    """
    Asks the user for confirmation using both TTS and a visual dialog.

    This function is crucial for security, ensuring that sensitive operations
    are explicitly approved by the user. It runs the dialog in a separate
    thread to prevent blocking issues with other UI elements or the TTS engine.

    Args:
        prompt_text: The question to ask the user.

    Returns:
        True if the user confirms (clicks "Yes"), False otherwise.
    """
    print(f"AIST Confirmation: {prompt_text}")
    # Speak the prompt to the user in a non-blocking way
    threading.Thread(target=speak, args=(prompt_text,), daemon=True).start()

    # Hide the root tkinter window
    root = tk.Tk()
    root.withdraw()
    # Ensure the dialog box appears on top of all other windows
    root.attributes("-topmost", True)

    confirmed = messagebox.askyesno(
        title="AIST - Permission Request",
        message=prompt_text
    )

    root.destroy()
    return confirmed