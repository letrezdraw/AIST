import speech_recognition as sr

# This script helps to determine the ambient noise energy level.
# Run this script in a quiet environment to get a baseline energy threshold.
# You can then use this value as a starting point for the 'energy_threshold' in your config.json.

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Please wait. Calibrating microphone for 1 second...")
    
    # Listen for 1 second to calibrate the energy threshold for ambient noise levels
    try:
        r.adjust_for_ambient_noise(source, duration=1)
        print(f"\nAmbient Noise Energy Threshold: {r.energy_threshold:.2f}")
        print("-" * 30)
        print("This is the threshold the application uses to start listening.")
        print("When you speak, the audio energy should be higher than this value.")
        print("\nSuggestions:")
        print("1. If this value is very high (e.g., > 1000) in a quiet room, your microphone might be too sensitive or have automatic gain control enabled.")
        print("2. You can use this value as a guide for setting the 'energy_threshold' in your 'config.json'. Start with a value slightly higher than this.")
        print("\nNow, the script will listen for a single phrase to show you the energy of your voice (for comparison).")

        print("\nPlease say something...")
        audio = r.listen(source)
        print("Processing...")
        
        # Simple RMS calculation to get an idea of the audio energy
        # This is not exactly what the library uses, but it's a good indicator.
        import audioop
        import math
        
        energy = audioop.rms(audio.get_raw_data(), audio.sample_width)
        print(f"Energy of your speech: {energy}")

        if energy > r.energy_threshold:
            print("\nYour speech energy is higher than the ambient noise threshold. This is good!")
        else:
            print("\nYour speech energy is lower than or close to the ambient noise threshold. This might be why your speech is not being detected properly.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Could not access the microphone. Please ensure it is connected and drivers are installed.")
