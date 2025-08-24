import requests
from typing import List, Tuple, Optional
from datetime import datetime
from flask import current_app

def build_fixed_prompt_from_preview(filename: str, preview_rows: list[dict]) -> str:
    # Build a stable prompt for the LLM using the CSV preview stored in DB.
    # The prompt requests 5–10 concise, actionable business insights.
    # It includes: filename, columns, and a few sample rows.

    # Derive header from preview rows (if any)
    header = list(preview_rows[0].keys()) if preview_rows else []

    # Start with clear instructions
    lines: list[str] = []
    lines.append("Analyze the following CSV sample and provide 5–10 concise business insights.")
    lines.append("Focus on trends, anomalies, seasonality, cohorts, and actionable suggestions.")
    lines.append("Output format: one bullet per line, no numbering, no code.")
    lines.append("")  # blank line for readability

    # Add file context
    lines.append(f"File name: {filename}")

    # Add columns
    if header:
        lines.append("Columns: " + ", ".join(map(str, header)))

    # Add sample rows (compact key=value format)
    if preview_rows:
        lines.append("Sample rows (truncated):")
        for row in preview_rows[:8]:
            # Keep key order aligned to header for consistency
            if header:
                kv = "; ".join(f"{col}={row.get(col)}" for col in header)
            else:
                # Fallback if no header (unlikely): iterate row items in insertion order
                kv = "; ".join(f"{k}={v}" for k, v in row.items())
            lines.append(" - " + kv)

    return "\n".join(lines)



def request_llm(prompt: str, timeout: int = 45) -> list[str]:
    """
    Send the given prompt to the LLM service and return a list of insights.
    Each insight is one line of text.
    """
    llm_api_url = "http://llm_service:5001/predict"

    try:
        # Send POST request with the prompt as JSON
        resp = requests.post(llm_api_url, json={"query": prompt}, timeout=timeout)
    except requests.exceptions.RequestException as e:
        # In case of network/connection error
        raise RuntimeError(f"Failed to contact LLM service: {e}")

    # Check HTTP status code
    if resp.status_code != 200:
        raise RuntimeError(f"LLM service error {resp.status_code}: {resp.text}")

    # Parse JSON response and extract the text
    data = resp.json()
    text = data.get("response", "") or ""

    # Split text into non-empty lines, clean bullet symbols
    insights = [ln.strip(" -•\t") for ln in text.splitlines() if ln.strip()]

    return insights



def generate_insights_for_any_file(user_id: str) -> tuple[str, list[str]]:
    """
    Pick any File from DB (ignores user for now), build a fixed prompt from its preview,
    call the LLM, and return (file_id, insights).
    """
    f = current_app.db.get_any_file()
    if not f:
        raise FileNotFoundError("לא נמצאו קבצים במערכת. נא להעלות קובץ תחילה.")

    preview_rows = f.preview or []
    prompt = build_fixed_prompt_from_preview(f.filename, preview_rows)

    insights = request_llm(prompt)
    if not insights:
        raise RuntimeError("שירות ה‑LLM לא החזיר תובנות.")

    # limit to a reasonable amount; can be adjusted later
    return f._id, insights[:12]

def generate_insights_for_file(file_id: str) -> tuple[str, list[str]]:
    """
    Given a file_id, fetch the File from DB, build a fixed prompt from its preview,
    call the LLM, and return (file_id, insights).
    """
    f = current_app.db.get_file(file_id)
    if not f:
        raise FileNotFoundError("Selected file not found in the system.")
    preview_rows = f.preview or []
    if not preview_rows:
        raise ValueError("Selected file has no preview available. Please re-upload the CSV.")
    prompt = build_fixed_prompt_from_preview(f.filename, preview_rows)
    insights = request_llm(prompt)
    if not insights:
        raise RuntimeError("LLM service returned no insights.")
    return f._id, insights[:12]

  