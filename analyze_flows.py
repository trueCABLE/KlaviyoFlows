# analyze_flows.py

import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def evaluate_subject_line(subject_line):
    """Use GPT to evaluate email subject lines for clarity, curiosity, urgency, and spamminess."""
    prompt = (
        f"Evaluate the following email subject line for marketing effectiveness:\n\n"
        f"Subject: \"{subject_line}\"\n\n"
        f"Rate its clarity, curiosity, urgency, and spam risk from 1–10.\n"
        f"Then suggest an improved version.\n"
        f"Return results as JSON format with keys: clarity, curiosity, urgency, spam_risk, suggestion."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        result = response['choices'][0]['message']['content']
        return result  # Return raw JSON-like text for now

    except Exception as e:
        return f"⚠️ Error evaluating subject line: {e}"

def analyze_flow_with_ai(flow_data, email_data):
    """
    Combines basic performance logic with AI feedback on subject lines.
    Args:
        flow_data (dict): Flow-level metadata
        email_data (list): List of emails with performance + subject lines
    Returns:
        list of flagged issues or AI suggestions
    """
    issues = []
    flow_name = flow_data.get("attributes", {}).get("name", "Unnamed Flow")

    for email in email_data:
        subject = email.get("subject", "N/A")
        open_rate = email.get("open_rate", 0.0)
        click_rate = email.get("click_rate", 0.0)

        print(f"🤖 Analyzing subject line: {subject}")
        ai_eval = evaluate_subject_line(subject)

        issues.append({
            "flow": flow_name,
            "subject": subject,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "ai_analysis": ai_eval
        })

    return issues
