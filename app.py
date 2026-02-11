import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import random
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Wyndham Points Dojo", page_icon="💎", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stButton>button {
        height: 3.5em;
        width: 100%;
        font-size: 24px !important;
        font-weight: bold;
        background-color: #005596;
        color: white;
        border-radius: 10px;
    }
    .big-stat {
        font-size: 30px;
        font-weight: bold;
        color: #005596;
        text-align: center;
        margin-bottom: 20px;
    }
    .vip-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
        border-left: 5px solid #005596;
    }
    /* SUCCESS VISUALS */
    .success-box {
        padding: 20px;
        background-color: #d1e7dd;
        color: #0f5132;
        border: 2px solid #badbcc;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- HARDCODED WYNDHAM DATA ---
POINTS_CHART = {
    "Ocean Walk - 2 BR Deluxe - Prime (July/Aug/Dec)": "325,000",
    "Ocean Walk - 2 BR Deluxe - High (Feb-June)": "300,000",
    "Bonnet Creek - 2 BR Deluxe - Prime": "224,000",
    "Las Vegas (Grand Desert) - 2 BR - Prime": "254,000",
    "Myrtle Beach (Seawatch) - 2 BR - High": "203,000",
    "Smokey Mountains (Great Smokies) - 2 BR - Prime": "238,000"
}

VIP_LEVELS = {
    "Silver": {"Points": "300k - 499k", "Discount": "25% off (60 days out)", "Upgrade": "1 Month window"},
    "Gold": {"Points": "500k - 799k", "Discount": "35% off (60 days out)", "Upgrade": "45 Day window"},
    "Platinum": {"Points": "800k+", "Discount": "50% off (60 days out)", "Upgrade": "60 Day window"}
}

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Dojo Settings")
    
    # API Key Handling (Crash Proof)
    api_key = None
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ API Key Loaded")
    except Exception:
        pass 

    if not api_key:
        api_key = st.text_input("Gemini API Key", type="password")

    # Mode Selection
    mode = st.radio("Training Mode:", ["🧠 Points Quiz (Memorize)", "💎 VIP Upsell Simulator"])
    
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# --- AI CONFIG ---
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

# --- MODE 1: POINTS QUIZ ---
if mode == "🧠 Points Quiz (Memorize)":
    st.title("🧠 Points Mastery Quiz")
    
    # 1. Initialize State Variables
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "quiz_state" not in st.session_state:
        st.session_state.quiz_state = "question" # "question" or "success"

    # 2. Pick a Question (Only if one doesn't exist)
    if "current_q" not in st.session_state:
        st.session_state.current_q = random.choice(list(POINTS_CHART.keys()))
        
        # LOCK THE OPTIONS SO THEY DON'T SHUFFLE WHILE YOU PLAY
        correct_answer = POINTS_CHART[st.session_state.current_q]
        all_values = list(POINTS_CHART.values())
        distractors = [v for v in all_values if v != correct_answer]
        
        # Pick 2 random wrong answers
        if len(distractors) < 2:
            current_options = [correct_answer, "154,000", "300,000"]
        else:
            current_options = random.sample(distractors, 2) + [correct_answer]
        
        random.shuffle(current_options)
        st.session_state.current_options = current_options

    # --- DISPLAY LOGIC ---
    
    if st.session_state.quiz_state == "success":
        # === VICTORY SCREEN (No Balloons) ===
        correct_val = POINTS_CHART[st.session_state.current_q]
        
        # The Green Card
        st.markdown(f"""
            <div class="success-box">
                ✅ CORRECT!<br>
                {st.session_state.current_q}<br>
                = {correct_val} Points
            </div>
        """, unsafe_allow_html=True)
        
        # Next Button
        if st.button("➡️ NEXT QUESTION"):
            # Reset for next round
            del st.session_state.current_q
            del st.session_state.current_options
            st.session_state.quiz_state = "question"
            st.rerun()

    else:
        # === QUESTION SCREEN ===
        st.info(f"Score: {st.session_state.quiz_score} | Question: How many points?")
        st.markdown(f"<div class='big-stat'>{st.session_state.current_q}</div>", unsafe_allow_html=True)
        
        correct_val = POINTS_CHART[st.session_state.current_q]
        opts = st.session_state.current_options
        
        col1, col2, col3 = st.columns(3)
        
        # Button Logic
        def check(val):
            if val == correct_val:
                st.session_state.quiz_score += 1
                st.session_state.quiz_state = "success"
                st.rerun()
            else:
                st.toast("❌ Wrong! Try again.", icon="💀")

        with col1:
            if st.button(opts[0]): check(opts[0])
        with col2:
            if st.button(opts[1]): check(opts[1])
        with col3:
            if st.button(opts[2]): check(opts[2])
            
        if st.button("Show Answer (I give up)"):
            st.warning(f"Answer: {correct_val}")

# --- MODE 2: VIP UPSELL SIMULATOR ---
elif mode == "💎 VIP Upsell Simulator":
    st.title("💎 VIP Closing Dojo")
    st.markdown("Pitch the **Value** of the next tier. Don't just list features.")
    
    target_tier = st.selectbox("Target Upgrade:", ["Silver (300k)", "Gold (500k)", "Platinum (800k)"])
    
    st.markdown(f"""
    <div class='vip-card'>
    <b>Selling: {target_tier}</b><br>
    Key Benefit 1: {VIP_LEVELS[target_tier.split()[0]]['Discount']}<br>
    Key Benefit 2: {VIP_LEVELS[target_tier.split()[0]]['Upgrade']}
    </div>
    """, unsafe_allow_html=True)
    
    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Audio Input
    audio_val = st.audio_input("Pitch the Upgrade")
    
    if audio_val:
        # User Audio Processing
        st.session_state.messages.append({"role": "user", "content": "🎤 [Pitch Sent]"})
        
        with st.spinner("Customer is thinking..."):
            try:
                if not api_key:
                    st.error("⚠️ Please enter API Key in sidebar first!")
                else:
                    audio_bytes = audio_val.read()
                    
                    # System Prompt for VIP Mode
                    sys_prompt = f"""
                    You are a SKEPTICAL Wyndham Owner. 
                    The user is trying to upgrade you to {target_tier}.
                    
                    **YOUR LOGIC:**
                    1. If they mention "More Points," say "I don't need more points."
                    2. If they mention "Discounts" ({VIP_LEVELS[target_tier.split()[0]]['Discount']}), say "That sounds interesting, tell me more."
                    3. If they mention "Upgrades" ({VIP_LEVELS[target_tier.split()[0]]['Upgrade']}), say "Wait, I can get a bigger room for free?"
                    
                    Keep responses short (1 sentence). Be tough but fair.
                    """
                    
                    prompt_parts = [sys_prompt, {"mime_type": "audio/wav", "data": audio_bytes}]
                    response = model.generate_content(prompt_parts)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    # TTS
                    tts = gTTS(text=response.text, lang='en')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format='audio/mp3', autoplay=True)
                    
                    st.info(f"Customer: {response.text}")
                
            except Exception as e:
                st.error(f"Error: {e}")
                
    # --- COACH BUTTON (RESTORED) ---
    st.divider()
    if st.button("👨‍🏫 Grade My Pitch"):
        with st.spinner("Sales Manager is reviewing tape..."):
            if not st.session_state.messages:
                st.error("Record a pitch first!")
            else:
                # Compile history
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                
                # Coach Prompt
                coach_prompt = f"""
                {history_text}
                
                You are a Sales Manager at Wyndham Ocean Walk. Analyze the rep's pitch above.
                Target Upgrade: {target_tier}
                
                1. Did they explain the VALUE of {target_tier} (Discounts/Windows) or just list features?
                2. Did they handle the customer's skepticism?
                3. Give 1 specific improvement.
                """
                
                try:
                    coach_resp = model.generate_content(coach_prompt)
                    st.success(coach_resp.text)
                except Exception as e:
                    st.error(f"Coach Error: {e}")