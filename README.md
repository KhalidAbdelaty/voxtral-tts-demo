# Voxtral TTS Demo

A Streamlit app for testing Mistral's [Voxtral TTS](https://mistral.ai/news/voxtral-tts) API. Built as a companion to the [DataCamp article on Voxtral TTS](https://www.datacamp.com/blog/voxtral-tts).

## Features

- **Text to Speech** — Generate speech from text using preset voices
- **Voice Cloning** — Clone a voice from a short audio reference (5-25 seconds)
- **Format Comparison** — Compare latency across output formats (PCM, MP3, WAV, FLAC, Opus)

## Setup

1. Clone this repository:

```bash
git clone https://github.com/KhalidAbdelaty/voxtral-tts-demo.git
cd voxtral-tts-demo
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your Mistral API key:

```bash
export MISTRAL_API_KEY="your-api-key-here"
```

You can get an API key from [console.mistral.ai](https://console.mistral.ai). Billing must be enabled on your account.

4. Run the app:

```bash
streamlit run app.py
```

## Requirements

- Python 3.9+
- A Mistral API key with billing enabled
- Voxtral TTS API access ($0.016 per 1,000 characters)

## Project Structure

```
voxtral-tts-demo/
├── app.py              # Streamlit application
├── requirements.txt    # Python dependencies
└── README.md
```

## License

MIT
