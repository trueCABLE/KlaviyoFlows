# main.py

import streamlit as st
import requests
import openai
import os
from dotenv import load_dotenv
import hashlib
import time

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
        
def get_flow_emails(flow_id, max_retries=3):
    url = f"{BASE_URL}/flows/{flow_id}/flow-actions"
    retries = 0

    while retries < max_retries:
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 429:
                wait = 2 ** retries
                st.warning(f"⏳ Rate limited. Retrying flow-actions in {wait}s...")
                time.sleep(wait)
                retries += 1
                continue

            response.raise_for_status()
            actions = response.json().get("data", [])

            email_steps = []

            for action in actions:
                action_type = action.get("attributes", {}).get("action_type", "")
                if action_type != "SEND_EMAIL":
                    continue

                action_id = action.get("id")
                message_url = f"{BASE_URL}/flow-actions/{action_id}/flow-messages"

                inner_retries = 0
                while inner_retries < 3:
                    msg_response = requests.get(message_url, headers=HEADERS)
                    if msg_response.status_code == 429:
                        wait = 2 ** inner_retries
                        st.warning(f"⏳ Rate limit hit fetching message {action_id}. Retrying in {wait}s...")
                        time.sleep(wait)
                        inner_retries += 1
                        continue
                    try:
                        msg_response.raise_for_status()
                        break  # success
                    except requests.exceptions.RequestException as e:
                        st.warning(f"⚠️ Failed to fetch message for action {action_id}: {e}")
                        break

                flow_messages = msg_response.json().get("data", []) if msg_response.ok else []
                if not flow_messages:
                    continue

                message = flow_messages[0]
                subject = message.get("attributes", {}).get("subject", "No subject")
                name = message.get("attributes", {}).get("name", "Unnamed Email")

                email_steps.append({
                    "name": name,
                    "subject": subject,
                    "id": action_id
                })

                time.sleep(0.25)  # 🕒 Slight delay to avoid rate limits

            return email_steps

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error fetching flow-actions for flow {flow_id}: {e}")
            return []

    st.error(f"❌ Failed to fetch emails for flow {flow_id} after {max_retries} retries.")
    return []

@st.cache_data(show_spinner=False)
def evaluate_subject_line(subject_line: str):
    """Use GPT to evaluate email subject lines and cache results."""
    # Generate a hash key for caching
    cache_key = hashlib.md5(subject_line.encode()).hexdigest()

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
    st.success(f"✅ Found {len(flows)} flows. Starting flow analysis...")
    
    progress_bar = st.progress(0)
    total_flows = len(flows)

    for i, flow in enumerate(flows):
        flow_id = flow["id"]
        flow_name = flow["attributes"]["name"]
        flow_status = flow["attributes"]["status"]

        start_time = time.perf_counter()

        with st.expander(f"📨 {flow_name} — [{flow_status}]"):
            try:
                emails = get_flow_emails(flow_id)
                
                elapsed = time.perf_counter() - start_time
                if elapsed > 15:
                    st.warning(f"⚠️ Skipped flow `{flow_name}` — took too long ({elapsed:.1f}s).")
                    continue

                if not emails:
                    st.info("No email steps found in this flow.")
                    continue

                for email in emails:
                    subject = email.get("subject", "No subject line")
                    email_name = email.get("name", "Unnamed Email")

                    st.markdown(f"### 📧 {email_name}")
                    st.markdown(f"**Subject:** `{subject}`")

                    with st.spinner("Analyzing with GPT..."):
                        result = evaluate_subject_line(subject)

                    st.markdown("**🤖 AI Feedback:**")
                    st.code(result, language="json")
                    st.markdown("---")
            except Exception as e:
                st.warning(f"⚠️ Error processing flow `{flow_name}`: {e}")

        progress_bar.progress((i + 1) / total_flows)
