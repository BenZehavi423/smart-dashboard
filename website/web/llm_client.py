import requests
from typing import List, Tuple, Optional
from datetime import datetime
from flask import current_app
import re

def request_llm(prompt: str, timeout: int = 45) -> list[str]:
    """
    Send the given prompt to the LLM service and return a list of insights.
    This function is now updated to robustly handle code block responses.
    """
    llm_api_url = "http://llm_service:5001/predict"

    try:
        resp = requests.post(llm_api_url, json={"query": prompt}, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to contact LLM service: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"LLM service error {resp.status_code}: {resp.text}")

    data = resp.json()
    text = data.get("response", "") or ""

    # --- NEW & IMPROVED LOGIC ---
    # Check if the response contains a Python code block
    code_block_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if code_block_match:
        # If a code block is found, extract and use only its content
        clean_code = code_block_match.group(1)
        insights = [line.strip() for line in clean_code.splitlines() if line.strip()]
    else:
        # Fallback to the original behavior if no code block is found
        insights = [ln.strip(" -•\t") for ln in text.splitlines() if ln.strip()]

    return insights

  