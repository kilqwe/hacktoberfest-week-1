import sounddevice as sd, soundfile as sf, numpy as np

DEVICE = 7
sr = int(sd.query_devices(DEVICE)["default_samplerate"])  # 44100

print("Recording 10s, play chirping now...")
rec = sd.rec(10 * sr, samplerate=sr, channels=1, device=DEVICE)
sd.wait()

print("Peak:", float(np.abs(rec).max()), "RMS:", float(np.sqrt((rec**2).mean())))
sf.write("test_dev7.wav", rec, sr)