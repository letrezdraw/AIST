# What are we doing?

We are building a real-time speech-to-text application using Python and the Whisper library.

## Current Status

The application is functional and can perform speech-to-text transcription. However, it is currently very sensitive to background noise. This leads to two main issues:

1.  **Inaccurate Transcriptions**: Background noise is sometimes picked up and transcribed as words, leading to "hallucinated" or incorrect output.
2.  **Constant Activation**: The application's listening function is often triggered by noise, causing it to process audio even when no one is speaking.

The current focus is to resolve this noise issue to make the transcription more reliable.

## Next Steps

The immediate next step is to implement a **real-time noise cancellation** feature. This will involve:

1.  Integrating a noise reduction library.
2.  Allowing the application to learn the characteristics of the background noise.
3.  Filtering out this noise from the microphone input before it is sent to the Whisper model for transcription.