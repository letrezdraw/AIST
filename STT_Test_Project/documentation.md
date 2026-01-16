# Application Documentation

This document provides a detailed explanation of the configuration settings available in the `config.json` file. You can modify these settings to fine-tune the application's performance and behavior.

The application will create a `config.json` file with default values on its first run.

## Configuration Settings (`config.json`)

### `whisper_model`
*   **Description**: Specifies the version of the Whisper model to use for transcription. Larger models are more accurate but slower and require more memory.
*   **Type**: `string`
*   **Default**: `"small"`
*   **Available Models**: `"tiny"`, `"base"`, `"small"`, `"medium"`, `"large"`. There are also English-only versions of the models, which can be faster if you are only transcribing English: `"tiny.en"`, `"base.en"`, `"small.en"`, `"medium.en"`.

### `language`
*   **Description**: The language of the speech to be transcribed. If set to `null` or an empty string, Whisper will attempt to auto-detect the language.
*   **Type**: `string`
*   **Default**: `"en"` (English)
*   **Example**: `"es"` for Spanish, `"ja"` for Japanese.

### `clear_log_on_start`
*   **Description**: If `true`, the `app.log` file will be cleared every time the application starts.
*   **Type**: `boolean`
*   **Default**: `true`

### `ffmpeg_path`
*   **Description**: The path to the `ffmpeg.exe` executable. By default, it is assumed to be in the project's root directory.
*   **Type**: `string`
*   **Default**: `"ffmpeg.exe"`

### `phrase_time_limit`
*   **Description**: The maximum number of seconds that the application will record a single phrase of speech. If you speak for longer than this limit, the recording will stop.
*   **Type**: `integer`
*   **Default**: `10`
*   **Suggestion**: If you find that your speech is being cut off, try increasing this value to `15` or `20`.

### `energy_threshold`
*   **Description**: The energy level above which audio is considered speech. This is the most important setting for controlling the microphone's sensitivity. It is only used when `use_dynamic_energy` is set to `false`. A higher value makes the microphone less sensitive.
*   **Type**: `integer`
*   **Default**: `305`
*   **Suggestion**: The `check_energy.py` script is provided to help you tune this value. Run it in your typical environment. It will show you the ambient noise energy and the energy of your voice. A good starting point for `energy_threshold` is a value between these two numbers. If the app is triggering on background noise, increase this value. If it's not picking up your voice, decrease it.

### `pause_threshold`
*   **Description**: The number of seconds of silence that will be considered the end of a phrase.
*   **Type**: `float`
*   **Default**: `0.8`
*   **Suggestion**: If you find that the application stops listening while you are pausing between words, try increasing this value to `1.5` or `2.0`.

### `listen_timeout`
*   **Description**: The number of seconds the application will wait for speech to start before timing out and listening again.
*   **Type**: `float`
*   **Default**: `1.6`

### `use_dynamic_energy`
*   **Description**: If `true`, the application will automatically adjust the `energy_threshold` based on the ambient noise level when the listening starts. This is a good general-purpose setting. However, if you are in an environment with inconsistent background noise, or if you want more manual control, set this to `false`.
*   **Type**: `boolean`
*   **Default**: `false`
*   **Suggestion**: For fine-tuning the sensitivity in a specific environment, it is recommended to set this to `false` and then manually tune the `energy_threshold` value.