# Trail Echo

Offline bird logger built on [BirdNET](https://github.com/birdnet-team/BirdNET-Analyzer).
It listens in 60-second chunks, identifies species locally, discards chunks with
no detections, and shows everything heard in a Streamlit dashboard.

Built for Hacktoberfest 2026, Week 1: Touch Grass. The idea is to leave the
device in your pocket during a walk and look at the results afterwards.

## How it works

capture audio → BirdNET analysis → CSV per chunk → Streamlit dashboard

- Chunks with no detections are deleted automatically (audio and CSV), so
  storage only grows when something is heard.
- All inference runs locally. No audio leaves your machine.

## Status

Tested: The microphone successfully captures the sound of the birds (captured using xeno-canto and youtube).
        Using BirdNET-Analyzer the app can successfully identify the bird species with confidence of >95%
Not yet tested: outdoor field recording on a real walk.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

The first BirdNET run downloads the model (about 224 MB).

## Usage

Start the logger (play bird audio on the laptop, or use a mic):

```bash
python trail.py
```

Analyze a phone recording (convert to WAV first, e.g. with ffmpeg):

```bash
ffmpeg -i walk.m4a -ar 48000 -ac 1 walk.wav
python analyze_walk.py walk.wav "2026-10-12 17:30"
```

Open the dashboard:

```bash
streamlit run app.py
```

## Known limitations

- Windows system-audio capture uses WASAPI loopback (`PyAudioWPatch`).
- Built-in laptop mics may apply noise suppression that mutes sustained sounds
  like birdsong. An external mic works better.
- Urban traffic noise reduces detection quality; a high-pass filter helps.
- One CSV per chunk; a SQLite store would scale better.

## Roadmap

- Open-and-go phone app with on-device inference
- GPS tagging and a map of where each species was heard
- Location and season filtering to cut false positives
- SQLite storage
- Raspberry Pi version with a USB mic

## License

Code: MIT. BirdNET's model is licensed CC BY-NC-SA 4.0, so this project is
for non-commercial use.
