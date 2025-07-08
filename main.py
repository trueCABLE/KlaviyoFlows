# main.py

import streamlit as st
import requests
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = "https://a.klaviyo.com/api"
HEADERS = {
    "Authorization": f"Klaviyo-API-Key {KLAVIYO_API_KEY}",
    "revision": "2023-10-15",
    "Content-Type": "application/json"
}
openai.api_key = OPENAI_API_KEY

# get_flows.py (or inside main.py if you’re keeping it all together)

def get_flow_emails(flow_id):
    url = f"{BASE_URL}/flows/{flow_id}/flow-actions"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        actions = response.json().get("data", [])
        return actions
    except Exception as e:
        st.error(f"Error fetching flow emails for {flow_id}: {e}")
        return []

def evaluate_subject_line(subject_line):
    prompt = (
        f"Evaluate the following email subject line for marketing effectiveness:\n\n"
        f"Subject: \"{subject_line}\"\n\n"
        f"Rate its CLARITY, CURIOSITY, URGENCY, and SPAM RISK from 1–10.\n"
        f"Then suggest an improved subject line.\n"
        f"Respond in JSON like this:\n"
        f"{{\"clarity\": x, \"curiosity\": x, \"urgency\": x, \"spam_risk\": x, \"suggestion\": \"...\"}}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI Error: {e}"


# === STREAMLIT UI ===
st.set_page_config(page_title="Klaviyo Flow + AI Subject Line Analyzer", layout="centered")

st.title("📩 Klaviyo Flow Viewer + 🤖 AI Subject Line Evaluator")

if not KLAVIYO_API_KEY:
    st.error("❗ KLAVIYO_API_KEY not set.")
    st.stop()

# --- Flow Fetching Section ---
with st.expander("🔍 View Klaviyo Flows"):
    limit = st.slider("How many flows to retrieve?", 1, 100, 25)
    if st.button("Fetch Flows"):
        flows = get_flows(limit)
        if flows:
            st.success(f"✅ Found {len(flows)} flows.")
            for flow in flows:
                st.subheader(flow['attributes']['name'])
                st.write(f"**ID:** {flow['id']}")
                st.write(f"**Status:** `{flow['attributes']['status']}`")
                st.markdown("---")
        else:
            st.warning("No flows returned.")

# --- Subject Line Evaluation ---
st.header("🧠 AI Subject Line Analyzer")

if not OPENAI_API_KEY:
    st.warning("OpenAI API key not set.")
else:
    subject_line = st.text_input("Enter an email subject line:")
    if st.button("Analyze Subject Line") and subject_line:
        with st.spinner("Analyzing with GPT..."):
            result = evaluate_subject_line(subject_line)
            st.text("📝 AI Feedback:")
            st.code(result, language="json")
