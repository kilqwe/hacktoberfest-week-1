import os
import sys
import subprocess
from datetime import datetime

import numpy as np
import soundfile as sf
import pyaudiowpatch as pyaudio

DURATION = 15  # keep short for testing, raise to 60 later
AUDIO_DIR = "audio_chunks"
RESULTS_DIR = "results"
MIN_CONF = "0.6"  # raise to 0.6 once detections work

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_loopback_device(p):
    wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    speakers = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
    if not speakers["isLoopbackDevice"]:
        for lb in p.get_loopback_device_info_generator():
            if speakers["name"] in lb["name"]:
                return lb
        raise RuntimeError("No loopback device found for default speakers")
    return speakers


def record_chunk(filename):
    print(f"Recording {DURATION} seconds of system audio to {filename}...")
    p = pyaudio.PyAudio()
    try:
        dev = get_loopback_device(p)
        sr = int(dev["defaultSampleRate"])
        ch = dev["maxInputChannels"]
        print(f"Using: {dev['name']} @ {sr} Hz, {ch} ch")

        stream = p.open(format=pyaudio.paInt16, channels=ch, rate=sr,
                        input=True, input_device_index=dev["index"],
                        frames_per_buffer=1024)

        frames = []
        for _ in range(int(sr / 1024 * DURATION)):
            frames.append(stream.read(1024, exception_on_overflow=False))
        stream.stop_stream()
        stream.close()
    finally:
        p.terminate()

    audio = np.frombuffer(b"".join(frames), dtype=np.int16).astype(np.float32) / 32768.0
    audio = audio.reshape(-1, ch).mean(axis=1)  # mono
    print("Peak:", float(np.abs(audio).max()))
    sf.write(filename, audio, sr)
    print("Recording complete.")


KEEP_AUDIO = True   # False = delete audio after analysis, keep only CSVs

def analyze_chunk(audio_file, out_dir):
    print(f"Running BirdNET on {audio_file}...")
    command = [
        sys.executable, "-m", "birdnet_analyzer.analyze",
        audio_file, "-o", out_dir,
        "--rtype", "csv", "--min_conf", MIN_CONF,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("BirdNET FAILED:", result.stderr)
        return

    base = os.path.splitext(os.path.basename(audio_file))[0]
    csv_path = os.path.join(out_dir, f"{base}.BirdNET.results.csv")

    has_detections = False
    if os.path.exists(csv_path):
        with open(csv_path) as f:
            has_detections = sum(1 for _ in f) > 1  # more than just the header

    if not has_detections:
        # nothing heard: drop the empty CSV and the audio
        if os.path.exists(csv_path):
            os.remove(csv_path)
        os.remove(audio_file)
        print("No detections, cleaned up.")
    elif not KEEP_AUDIO:
        os.remove(audio_file)
        print("Detections saved, audio removed.")
    else:
        print("Detections saved, audio kept.")

if __name__ == "__main__":
    print("Starting Offline Trail Logger...")
    try:
        while True:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = os.path.join(AUDIO_DIR, f"chunk_{timestamp}.wav")
            record_chunk(audio_path)
            analyze_chunk(audio_path, RESULTS_DIR)
    except KeyboardInterrupt:
        print("\nLogging stopped.")