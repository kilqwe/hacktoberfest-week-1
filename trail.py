import sounddevice as sd
import soundfile as sf
import os
import sys
import subprocess
from datetime import datetime

DURATION = 15
SAMPLE_RATE = 48000
AUDIO_DIR = "audio_chunks"
RESULTS_DIR = "results"
MIN_CONF = "0.6"  # raise to 0.6 once detections work

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def record_chunk(filename):
    print(f"Recording {DURATION} seconds to {filename}...")
    recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    sf.write(filename, recording, SAMPLE_RATE)
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
        
try:
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = os.path.join(AUDIO_DIR, f"chunk_{timestamp}.wav")

        record_chunk(audio_path)
        analyze_chunk(audio_path, RESULTS_DIR)
except KeyboardInterrupt:
    print("\nLogging stopped. Time to check the dashboard!")