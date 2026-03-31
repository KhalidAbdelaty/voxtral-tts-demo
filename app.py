"""
Voxtral TTS Demo App
A Streamlit interface for testing Mistral's Voxtral TTS API.
Covers basic speech generation, voice cloning, and format comparison.

Usage:
    pip install -r requirements.txt
    export MISTRAL_API_KEY="your-api-key-here"
    streamlit run app.py
"""

import base64
import io
import os
import time

import streamlit as st
from mistralai.client import Mistral


# Nine supported languages with sample text in each
LANGUAGES = {
    "English":    {"code": "en", "sample": "Welcome to Voxtral TTS. This is a speech generation demo."},
    "French":     {"code": "fr", "sample": "Bienvenue sur Voxtral TTS. Ceci est une démonstration de synthèse vocale."},
    "German":     {"code": "de", "sample": "Willkommen bei Voxtral TTS. Dies ist eine Sprachgenerations-Demo."},
    "Spanish":    {"code": "es", "sample": "Bienvenido a Voxtral TTS. Esta es una demostración de síntesis de voz."},
    "Dutch":      {"code": "nl", "sample": "Welkom bij Voxtral TTS. Dit is een spraakgeneratiedemo."},
    "Portuguese": {"code": "pt", "sample": "Bem-vindo ao Voxtral TTS. Esta é uma demonstração de síntese de voz."},
    "Italian":    {"code": "it", "sample": "Benvenuto su Voxtral TTS. Questa è una demo di sintesi vocale."},
    "Hindi":      {"code": "hi", "sample": "Voxtral TTS में आपका स्वागत है। यह एक वाक् उत्पादन डेमो है।"},
    "Arabic":     {"code": "ar", "sample": "مرحباً بكم في Voxtral TTS. هذا عرض توضيحي لتوليد الكلام."},
}


# --- Session State ---

def init_session_state():
    defaults = {
        "client": None,
        "voices": [],
        "cloned_voice_id": None,
        "cloned_voice_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --- Client Setup ---

def get_client():
    """Initialize and cache the Mistral client."""
    if st.session_state.client is None:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            return None
        st.session_state.client = Mistral(api_key=api_key)
    return st.session_state.client


def load_voices(client):
    """Fetch available voices from the API."""
    if not st.session_state.voices:
        try:
            result = client.audio.voices.list()
            st.session_state.voices = result.items if result.items else []
        except Exception as e:
            st.error(f"Failed to load voices: {e}")
    return st.session_state.voices


# --- Tab 1: Basic TTS ---

def render_basic_tts(client):
    st.subheader("Generate speech from text")
    st.write(
        "Select a voice and language, then type your text. "
        "The model supports nine languages natively."
    )

    voices = load_voices(client)
    if not voices:
        st.warning("No voices found. Create one in the Voice Cloning tab first.")
        return

    voice_options = {v.name: v.id for v in voices}
    selected_name = st.selectbox("Voice", list(voice_options.keys()))
    voice_id = voice_options[selected_name]

    selected_language = st.selectbox("Language", list(LANGUAGES.keys()), index=0)
    sample_text = LANGUAGES[selected_language]["sample"]

    text_input = st.text_area(
        "Text to speak",
        value=sample_text,
        height=100,
        key=f"basic_text_{selected_language}",
    )

    output_format = st.selectbox(
        "Output format",
        ["mp3", "wav", "pcm", "flac", "opus"],
        index=0,
    )

    if st.button("Generate Speech", type="primary", key="btn_basic"):
        if not text_input.strip():
            st.warning("Please enter some text.")
            return

        with st.spinner("Generating audio..."):
            try:
                start = time.time()
                response = client.audio.speech.complete(
                    model="voxtral-mini-tts-2603",
                    input=text_input,
                    voice_id=voice_id,
                    response_format=output_format,
                )
                elapsed = time.time() - start

                audio_bytes = base64.b64decode(response.audio_data)
                st.success(f"Generated in {elapsed:.2f}s")

                # Audio player (works with mp3, wav, flac)
                if output_format in ("mp3", "wav", "flac"):
                    st.audio(audio_bytes, format=f"audio/{output_format}")

                # Download button
                st.download_button(
                    label=f"Download .{output_format}",
                    data=audio_bytes,
                    file_name=f"voxtral_output.{output_format}",
                    mime=f"audio/{output_format}",
                )

            except Exception as e:
                st.error(f"Generation failed: {e}")


# --- Tab 2: Voice Cloning ---

def render_voice_cloning(client):
    st.subheader("Clone a voice from reference audio")
    st.write(
        "Upload a short audio clip (5-25 seconds recommended) "
        "and the model will create a voice profile that captures "
        "the speaker's accent, tone, and rhythm."
    )

    uploaded_file = st.file_uploader(
        "Reference audio",
        type=["mp3", "wav", "flac", "ogg"],
        help="Best results with 8-15 seconds of clear speech.",
    )

    voice_name = st.text_input("Voice name", value="my-cloned-voice")

    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox(
            "Language",
            list(LANGUAGES.keys()),
            index=0,
            key="clone_language",
        )
    with col2:
        gender = st.selectbox("Gender", ["male", "female"], index=0)

    if st.button("Create Voice", type="primary", key="btn_clone"):
        if not uploaded_file:
            st.warning("Please upload a reference audio file.")
            return

        with st.spinner("Creating voice profile..."):
            try:
                audio_bytes = uploaded_file.read()
                sample_b64 = base64.b64encode(audio_bytes).decode()

                voice = client.audio.voices.create(
                    name=voice_name,
                    sample_audio=sample_b64,
                    sample_filename=uploaded_file.name,
                    languages=[LANGUAGES[language]["code"]],
                    gender=gender,
                )

                st.session_state.cloned_voice_id = voice.id
                st.session_state.cloned_voice_name = voice.name
                # Refresh voice list
                st.session_state.voices = []

                st.success(f"Voice created: {voice.name} (ID: {voice.id})")

            except Exception as e:
                st.error(f"Voice creation failed: {e}")

    # Generate with cloned voice
    if st.session_state.cloned_voice_id:
        st.divider()
        st.write(f"**Active cloned voice:** {st.session_state.cloned_voice_name}")

        clone_text = st.text_area(
            "Text to speak with cloned voice",
            value="This sentence was generated using a cloned voice from a short reference clip.",
            height=100,
            key="clone_text",
        )

        if st.button("Generate with Cloned Voice", key="btn_clone_gen"):
            with st.spinner("Generating..."):
                try:
                    response = client.audio.speech.complete(
                        model="voxtral-mini-tts-2603",
                        input=clone_text,
                        voice_id=st.session_state.cloned_voice_id,
                        response_format="mp3",
                    )
                    audio_bytes = base64.b64decode(response.audio_data)
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="Download cloned output",
                        data=audio_bytes,
                        file_name="cloned_output.mp3",
                        mime="audio/mp3",
                        key="dl_clone",
                    )
                except Exception as e:
                    st.error(f"Generation failed: {e}")


# --- Tab 3: Format Comparison ---

def measure_streaming_latency(client, voice_id, text, fmt):
    """Return (time_to_first_chunk, audio_bytes) using streaming mode."""
    start = time.time()
    stream = client.audio.speech.complete(
        model="voxtral-mini-tts-2603",
        input=text,
        voice_id=voice_id,
        response_format=fmt,
        stream=True,
    )
    first_chunk_time = None
    buf = io.BytesIO()
    for chunk in stream:
        if first_chunk_time is None:
            first_chunk_time = time.time() - start
        if hasattr(chunk, "data") and hasattr(chunk.data, "audio_data") and chunk.data.audio_data:
            buf.write(base64.b64decode(chunk.data.audio_data))
    return first_chunk_time, buf.getvalue()


def render_format_comparison(client):
    st.subheader("Compare output format latency")
    st.write(
        "Measures time-to-first-audio-chunk in streaming mode. "
        "PCM skips compression entirely, which is why it arrives faster. "
        "MP3 adds encoding overhead before the first chunk is ready. "
        "Note: the audio player below requires the full file before playback, "
        "so it will not start at the latency shown. These numbers reflect "
        "what a voice agent pipeline would see when piping chunks directly to a speaker."
    )

    voices = load_voices(client)
    if not voices:
        st.warning("No voices found. Create one in the Voice Cloning tab first.")
        return

    voice_options = {v.name: v.id for v in voices}
    selected_name = st.selectbox(
        "Voice for comparison", list(voice_options.keys()), key="fmt_voice"
    )
    voice_id = voice_options[selected_name]

    comparison_text = st.text_area(
        "Text for comparison",
        value="This is a latency test comparing different output formats from Voxtral TTS.",
        height=80,
        key="fmt_text",
    )

    formats_to_test = st.multiselect(
        "Formats to compare",
        ["pcm", "mp3", "wav", "flac", "opus"],
        default=["pcm", "mp3"],
    )

    if st.button("Run Comparison", type="primary", key="btn_fmt"):
        if len(formats_to_test) < 2:
            st.warning("Select at least two formats to compare.")
            return

        results = {}
        progress = st.progress(0)

        for i, fmt in enumerate(formats_to_test):
            with st.spinner(f"Testing {fmt}..."):
                try:
                    first_chunk_time, audio_bytes = measure_streaming_latency(
                        client, voice_id, comparison_text, fmt
                    )
                    results[fmt] = {
                        "latency": first_chunk_time,
                        "size_kb": len(audio_bytes) / 1024,
                        "audio": audio_bytes,
                    }
                except Exception as e:
                    results[fmt] = {"error": str(e)}

            progress.progress((i + 1) / len(formats_to_test))

        progress.empty()

        # Display results
        st.divider()
        st.write("**Results**")

        for fmt, data in results.items():
            if "error" in data:
                st.error(f"{fmt.upper()}: {data['error']}")
                continue

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.metric(f"{fmt.upper()} latency", f"{data['latency']:.2f}s")
            with col2:
                st.metric("File size", f"{data['size_kb']:.1f} KB")
            with col3:
                if fmt in ("mp3", "wav", "flac"):
                    st.audio(data["audio"], format=f"audio/{fmt}")

        # Summary
        valid = {k: v for k, v in results.items() if "error" not in v}
        if len(valid) >= 2:
            fastest = min(valid, key=lambda k: valid[k]["latency"])
            slowest = max(valid, key=lambda k: valid[k]["latency"])
            diff = valid[slowest]["latency"] - valid[fastest]["latency"]
            st.info(
                f"**{fastest.upper()}** was fastest. "
                f"**{slowest.upper()}** was {diff:.2f}s slower."
            )
        st.caption("Latency = time to first audio chunk in streaming mode.")


# --- Main ---

def main():
    st.set_page_config(
        page_title="Voxtral TTS Demo",
        page_icon="🔊",
        layout="centered",
    )

    st.title("🔊 Voxtral TTS Demo")
    st.caption(
        "A companion app for the DataCamp tutorial on Mistral's Voxtral TTS. "
        "Generate speech, clone voices, and compare output formats."
    )

    init_session_state()
    client = get_client()

    if client is None:
        st.error(
            "**MISTRAL_API_KEY not set.** "
            "Run `export MISTRAL_API_KEY='your-key'` before starting the app."
        )
        st.info(
            "Get your API key from [console.mistral.ai](https://console.mistral.ai). "
            "You will need billing enabled on your account."
        )
        return

    tab1, tab2, tab3 = st.tabs([
        "🗣️ Text to Speech",
        "🎭 Voice Cloning",
        "⚡ Format Comparison",
    ])

    with tab1:
        render_basic_tts(client)

    with tab2:
        render_voice_cloning(client)

    with tab3:
        render_format_comparison(client)

    st.divider()
    st.caption(
        "Powered by [Voxtral TTS](https://mistral.ai/news/voxtral-tts) "
        "| Built with [Streamlit](https://streamlit.io)"
    )


if __name__ == "__main__":
    main()
