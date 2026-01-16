# Future Plans and Potential Improvements

This document outlines potential features and improvements that could be added to the application in the future.

## Immediate Goals

*   **Implement Real-time Noise Cancellation**: This is the highest priority task. The plan is to use a library like `noisereduce` to filter out background noise from the microphone audio in real-time. This will involve creating a noise profile from the ambient sound and then using that profile to clean the audio that is fed to the Whisper model.

## Core Functionality Enhancements

*   **Advanced Noise Cancellation**: While the initial implementation of noise cancellation will be based on spectral gating (`noisereduce`), more advanced techniques using deep learning models could be explored for even better performance.
*   **Voice Activity Detection (VAD)**: A more sophisticated VAD could be implemented to more accurately detect human speech and avoid transcribing non-speech sounds. This could replace the current energy threshold-based system entirely.
*   **Diarization**: The ability to distinguish between different speakers in the audio and label the transcribed text accordingly.
*   **Automatic Punctuation**: The Whisper model can be prompted to produce more natural punctuation. This could be explored and made a configurable option.
*   **Real-time Output**: Currently, the transcription is displayed after a phrase is complete. A more advanced implementation could show the transcribed text as it is being spoken.

## User Interface and Experience

*   **UI Redesign**: The current UI is very basic. A more modern and user-friendly interface could be designed using a different GUI framework or by improving the existing one.
*   **System Tray Icon**: The application could run as an icon in the system tray for easier access and background operation.
*   **Selectable Microphone**: An option to choose the input microphone from a list of available devices.
*   **Visual Feedback**: A visual indicator (e.g., a VU meter) to show the current microphone volume and energy level.

## Other

*   **Export/Save Transcription**: An option to save the full transcription to a text file.
*   **Cross-platform Installer**: Create installers for Windows, macOS, and Linux to make the application easier to distribute and install.
*   **Plugin System**: A plugin architecture that would allow other developers to extend the application with new features.