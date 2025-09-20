import os
import torch
import soundfile as sf
from voxcpm import VoxCPM

# --- Configuration ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_ID = "openbmb/VoxCPM-0.5B"
# --- End Configuration ---

# --- Global Model Cache ---
VOXCPM_MODEL = None

def _load_model():
    """Loads the VoxCPM model into memory."""
    global VOXCPM_MODEL
    if VOXCPM_MODEL is None:
        print(f"Loading VoxCPM model '{MODEL_ID}'... This may take a moment.")
        try:
            VOXCPM_MODEL = VoxCPM.from_pretrained(MODEL_ID)
            print("VoxCPM model loaded successfully.")
        except Exception as e:
            print(f"Failed to load VoxCPM model: {e}")
            raise
    return VOXCPM_MODEL

def clone_voice(text: str, reference_audio_path: str, output_filename: str) -> str | None:
    """
    Clones a voice from a reference audio file to speak the given text using VoxCPM.
    """
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, output_filename)

    if not os.path.exists(reference_audio_path):
        print(f"Error: Reference audio file not found at {reference_audio_path}")
        return None

    try:
        model = _load_model()
        if model is None: return None

        print(f"Generating voice for text: '{text[:40]}...'")

        # VoxCPM requires a transcript for the prompt audio.
        # For now, we'll use a generic placeholder.
        # A more advanced implementation might use Speech-to-Text here.
        prompt_transcript = "..."

        wav = model.generate(
            text=text,
            prompt_wav_path=reference_audio_path,
            prompt_text=prompt_transcript,
            denoise=True,
            inference_timesteps=10
        )

        sf.write(output_path, wav, 16000)

        print(f"Voiceover successfully generated at: {output_path}")
        return output_path

    except Exception as e:
        print(f"An error occurred during voice cloning with VoxCPM: {e}")
        return None

if __name__ == '__main__':
    print("--- VoxCPM Voice Cloning Module Test ---")

    dummy_audio_dir = "downloads/audio"
    dummy_audio_path = os.path.join(dummy_audio_dir, "reference.wav")
    if not os.path.exists(dummy_audio_path):
        print("Creating a dummy reference audio file for testing.")
        if not os.path.exists(dummy_audio_dir):
            os.makedirs(dummy_audio_dir)
        import numpy as np
        sr = 16000
        duration = 2
        frequency = 440
        t = np.linspace(0., duration, int(sr * duration), endpoint=False)
        amplitude = np.iinfo(np.int16).max * 0.1
        data = amplitude * np.sin(2. * np.pi * frequency * t)
        sf.write(dummy_audio_path, data.astype(np.int16), sr)
        print(f"Dummy file created at {dummy_audio_path}")

    english_script = "Hello world, this is a test of the voice cloning system."

    try:
        generated_file = clone_voice(
            text=english_script,
            reference_audio_path=dummy_audio_path,
            output_filename="voxcpm_test_output.wav"
        )

        if generated_file and os.path.exists(generated_file):
            print(f"\nTest successful. Output file is at: {generated_file}")
        else:
            print("\nTest failed. See error messages above.")

    except Exception as e:
        print(f"\nTest execution failed with an exception: {e}")

    print("--- End of Test ---")
