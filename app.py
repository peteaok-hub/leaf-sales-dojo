import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import random
import io
import os

# --- PAGE CONFIGURATION (Mobile Optimized) ---
st.set_page_config(page_title="Wyndham Owner Dojo", page_icon="🏖️", layout="centered")

# --- CSS FOR "DRIVE MODE" ---
st.markdown("""
    <style>
    .stButton>button {
        height: 4em;
        width: 100%;
        font-size: 28px !important;
        font-weight: bold;
        background-color: #005596; /* Wyndham Blue */
        color: white;
        border-radius: 12px;
    }
    .stMarkdown h1 {
        font-size: 2.5rem !important;
        text-align: center;
        color: #005596;
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
    
    # 1. API KEY HANDLING
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Key Loaded")
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    # 2. WYNDHAM PERSONAS
    persona_type = st.selectbox(
        "Owner Type:",
        [
            "The 'Happy' Owner (Hardest - Doesn't want more)", 
            "The 'Frustrated' Booker (Can't get dates)", 
            "The 'Maintenance Fee' Hater", 
            "The 'RCI' Trader (Confused)"
        ]
    )
    
    # Chaos Mode (RNG)
    if "mood" not in st.session_state:
        st.session_state.mood = random.choice(["Skeptical", "Rushed", "Annoyed", "Relaxed but Cheap"])
    
    st.info(f"Current Mood: {st.session_state.mood}")
    
    if st.button("Reset / Next Owner"):
        st.session_state.messages = []
        st.session_state.mood = random.choice(["Skeptical", "Rushed", "Annoyed", "Relaxed but Cheap"])
        st.rerun()

# --- SYSTEM PROMPT (THE BRAIN) ---
SYSTEM_PROMPT = f"""
You are roleplaying as a WYNDHAM OWNER named 'Robert' or 'Karen' at the Ocean Walk Resort in Daytona Beach.
You are in an "Owner Update" meeting with a Sales Rep (the user).
You currently own 200,000 Points (Standard Status).

**YOUR PERSONA:** {persona_type}
**YOUR MOOD:** {st.session_state.mood}

**YOUR OBJECTIONS (Use these):**
1. "We have enough points. We barely use what we have."
2. "The maintenance fees are already too high. I'm not paying more."
3. "I tried to book Christmas last year and it was full. Buying more points won't fix that."
4. "I'm actually thinking of selling my timeshare, not buying more."

**WIN CONDITION (When to agree):**
You are stubborn. You will ONLY start to listen/agree if the Rep explains how **VIP STATUS (Silver/Gold)** gives you the **13-Month Booking Window** or **Room Upgrades**. 
If they just talk about "more vacations," shut them down.
If they talk about "Access" and "Fixing the Availability," get interested.

**INSTRUCTIONS:**
1. Listen to the audio input from the user.
2. Respond verbally (short, natural, 1-2 sentences max).
3. Do not be polite. Be a real customer who wants to get back to the beach.
4. Do not describe actions (like *sighs*), just speak the dialogue.
"""

# --- APP HEADER ---
st.title("🏖️ Wyndham Owner Dojo")
st.markdown(f"<div style='text-align: center; font-size: 18px; margin-bottom: 20px;'>Pitching to: <b>{persona_type}</b><br>Mood: <b>{st.session_state.mood}</b></div>", unsafe_allow_html=True)

# Initialize History
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# Configure AI
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.warning("⚠️ Enter API Key in Sidebar to Start")
    st.stop()

# --- AUDIO INPUT (THE MIC) ---
st.markdown("### 👇 Tap Mic to Pitch")
audio_value = st.audio_input("Record")

if audio_value:
    # 1. Add User Audio Placeholder
    st.session_state.messages.append({"role": "user", "content": "🎤 [Audio Sent]"})
    
    with st.spinner("Owner is thinking..."):
        try:
            # 2. Send Audio directly to Gemini
            audio_bytes = audio_value.read()
            
            # Build prompt with history
            prompt_parts = [SYSTEM_PROMPT]
            for msg in st.session_state.messages[-4:]: # Keep last 4 turns for context
                if msg["content"] != "🎤 [Audio Sent]":
                    prompt_parts.append(f"{msg['role']}: {msg['content']}")
            
            prompt_parts.append({"mime_type": "audio/wav", "data": audio_bytes})
            prompt_parts.append("Respond to this audio as the Wyndham Owner.")

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
    st.markdown("### 🔊 Owner Response:")
    st.audio(st.session_state.last_audio, format='audio/mp3', autoplay=True)
    
    # Display text for reference
    if st.session_state.messages:
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "assistant":
            st.info(f"Owner: {last_msg['content']}")

# --- COACH BUTTON ---
st.divider()
if st.button("👨‍🏫 Grade My Pitch"):
    with st.spinner("Sales Manager is reviewing tape..."):
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        coach_prompt = f"""
        {history_text}
        
        Analyze my sales pitch for Wyndham Vacation Ownership.
        1. Did I find the 'Pain' (Availability/Booking issues)?
        2. Did I pivot to VIP Status/Access instead of just "selling points"?
        3. Did I handle the "Maintenance Fee" objection correctly (Value vs. Cost)?
        
        Give me 1 specific tip to close better next time.
        """
        coach_resp = model.generate_content(coach_prompt)
        st.success(coach_resp.text)