import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import random
import io
import os

# --- PAGE CONFIGURATION (Mobile Optimized) ---
st.set_page_config(page_title="Leaf Sales Dojo", page_icon="🚘", layout="centered")

# --- CSS FOR "DRIVE MODE" ---
st.markdown("""
    <style>
    .stButton>button {
        height: 4em;
        width: 100%;
        font-size: 28px !important;
        font-weight: bold;
        background-color: #ff4b4b;
        color: white;
        border-radius: 12px;
    }
    .stMarkdown h1 {
        font-size: 2.5rem !important;
        text-align: center;
    }
    .stAudioInput {
        transform: scale(1.3);
        margin-bottom: 20px;
    }
    /* Hide the top header/hamburger menu to look like an app */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. API KEY HANDLING (Secrets First, then Input)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Key Loaded from Cloud Secrets")
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    persona_type = st.selectbox(
        "Opponent:",
        ["The Grumpy Skeptic (Robert)", "The 'Price' Shopper", "The 'Talk to Spouse' Staller", "The 'DIY' Handyman"]
    )
    
    # Chaos Mode (RNG)
    if "mood" not in st.session_state:
        st.session_state.mood = random.choice(["Impatient", "Curious", "Angry", "Tired", "Suspicious"])
    
    st.info(f"Current Mood: {st.session_state.mood}")
    
    if st.button("Reset / New Customer"):
        st.session_state.messages = []
        st.session_state.mood = random.choice(["Impatient", "Curious", "Angry", "Tired", "Suspicious"])
        st.rerun()

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
You are roleplaying as a HOMEOWNER named 'Robert' in Volusia County, FL.
You are speaking to a Salesperson (the user) who is trying to sell you a Leaf Home Bathroom Remodel.

**YOUR PERSONA:** {persona_type}
**YOUR MOOD:** {st.session_state.mood}

**INSTRUCTIONS:**
1. Listen to the audio input from the user.
2. Respond verbally (short, 1-2 sentences max).
3. BE DIFFICULT. Raise objections about price ($15k is too much), trust, or spouse.
4. Only agree if the user makes a compelling point about "Structural Water Damage" (Subfloor).
5. Do not describe your actions (like *coughs*), just speak the dialogue.
"""

# --- APP HEADER ---
st.title("🚘 Leaf Sales Dojo")
st.markdown(f"<div style='text-align: center; font-size: 20px; margin-bottom: 20px;'>Vs. <b>{persona_type}</b><br>Mood: <b>{st.session_state.mood}</b></div>", unsafe_allow_html=True)

# Initialize History
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# Configure AI
if api_key:
    genai.configure(api_key=api_key)
    # UPDATED: Using the 2.5 model that works with your key
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.warning("⚠️ Waiting for API Key...")
    st.stop()

# --- AUDIO INPUT (THE MIC) ---
st.markdown("### 👇 Tap Mic to Fight")
audio_value = st.audio_input("Record")

if audio_value:
    # 1. Add User Audio Placeholder
    st.session_state.messages.append({"role": "user", "content": "🎤 [Audio Sent]"})
    
    with st.spinner("Robert is thinking..."):
        try:
            # 2. Send Audio directly to Gemini
            audio_bytes = audio_value.read()
            
            # Build prompt with recent history
            prompt_parts = [SYSTEM_PROMPT]
            for msg in st.session_state.messages[-4:]:
                if msg["content"] != "🎤 [Audio Sent]":
                    prompt_parts.append(f"{msg['role']}: {msg['content']}")
            
            prompt_parts.append({"mime_type": "audio/wav", "data": audio_bytes})
            prompt_parts.append("Respond to this audio.")

            # Generate Response
            response = model.generate_content(prompt_parts)
            ai_text = response.text

            # 3. Add AI Text to History
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

            # 4. Convert AI Text to Audio (TTS)
            tts = gTTS(text=ai_text, lang='en', slow=False)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.session_state.last_audio = audio_fp.getvalue()
            
        except Exception as e:
            st.error(f"Error: {e}")

# --- DISPLAY OUTPUT (Big Audio Player) ---
if st.session_state.last_audio:
    st.markdown("### 🔊 Response:")
    st.audio(st.session_state.last_audio, format='audio/mp3', autoplay=True)
    
    # Display text for reference
    if st.session_state.messages:
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "assistant":
            st.info(f"Robert: {last_msg['content']}")

# --- COACH BUTTON ---
st.divider()
if st.button("👨‍🏫 Grade My Pitch"):
    with st.spinner("Coach is listening..."):
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        coach_resp = model.generate_content(f"{history_text}\n\nAnalyze my sales pitch. Was I confident? Did I pivot to the subfloor issue? Give me 1 tip.")
        st.success(coach_resp.text)