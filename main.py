# main.py

import streamlit as st
import requests
import openai
import os
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Set API keys ===
openai.api_key = OPENAI_API_KEY
BASE_URL = "https://a.klaviyo.com/api"
HEADERS = {
    "Authorization": f"Klaviyo-API-Key {KLAVIYO_API_KEY}",
    "revision": "2023-10-15",
    "Content-Type": "application/json"
}


# === Functions ===
def get_flows(limit=25):
    url = f"{BASE_URL}/flows/?page[size]={limit}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        st.error(f"❌ Error fetching flows: {e}")
        return []


def get_flow_emails(flow_id):
    url = f"{BASE_URL}/flows/{flow_id}/flow-actions"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        actions = response.json().get("data", [])
        return [a for a in actions if a['attributes']['action_type'] == 'EMAIL']
    except Exception as e:
        st.error(f"❌ Error fetching emails for flow {flow_id}: {e}")
        return []


def evaluate_subject_line(subject_line):
    prompt = (
        f"Evaluate the following email subject line for marketing effectiveness:\n\n"
        f"Subject: \"{subject_line}\"\n\n"
        f"Rate its clarity, curiosity, urgency, and spam risk from 1–10.\n"
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
        return f"⚠️ OpenAI error: {e}"


# === Streamlit UI ===
st.set_page_config(page_title="Klaviyo + AI Subject Line Analyzer", layout="wide")

st.title("📩 Klaviyo Flow Viewer + 🤖 AI Subject Line Evaluator")

if not KLAVIYO_API_KEY:
    st.error("KLAVIYO_API_KEY not set.")
    st.stop()
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not set.")
    st.stop()

# === Flow Viewer ===
st.header("🔍 View Your Klaviyo Flows")

limit = st.slider("How many flows to fetch?", 1, 100, 25)
flows = []

if st.button("Fetch Flows"):
    with st.spinner("Loading flows from Klaviyo..."):
        flows = get_flows(limit)

if flows:
    for flow in flows:
        flow_id = flow["id"]
        flow_name = flow["attributes"]["name"]
        flow_status = flow["attributes"]["status"]

        with st.expander(f"📨 {flow_name} — [{flow_status}]"):
            emails = get_flow_emails(flow_id)

            if not emails:
                st.info("No email steps found in this flow.")
                continue

            for email in emails:
                subject = email["attributes"].get("subject", "No subject line")
                email_name = email["attributes"].get("name", "Unnamed Email")
                st.markdown(f"**📧 {email_name}**")
                st.markdown(f"*Subject:* `{subject}`")

                if st.button(f"Analyze Subject", key=f"{flow_id}_{email['id']}"):
                    with st.spinner("Analyzing with GPT..."):
                        result = evaluate_subject_line(subject)
                        st.text("📊 AI Feedback:")
                        st.code(result, language="json")
