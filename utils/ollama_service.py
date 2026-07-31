"""
utils/ollama_service.py — Reusable Ollama API wrapper.

Provides:
  - ensure_ollama_running() → bool   (auto-starts Ollama if needed)
  - is_ollama_available()  → bool
  - build_machine_context()  → dict
  - generate_report()        → Iterator[str]  (streams tokens)
  - chat()                   → Iterator[str]  (streams tokens)
"""

import json
import subprocess
import sys
import time
import requests
from typing import Iterator

OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# Timeout for streaming requests (seconds)
_STREAM_TIMEOUT = 180

# How long to wait (seconds) for Ollama to become available after launching it
_STARTUP_TIMEOUT = 15


# ── Auto-start ────────────────────────────────────────────────────────────

def ensure_ollama_running() -> bool:
    """
    Ensure Ollama is running before the app tries to use it.

    1. If Ollama is already reachable, return True immediately.
    2. If not, launch ``ollama serve`` as a background process:
       - On Windows: uses CREATE_NO_WINDOW + DETACHED_PROCESS flags so no
         console window appears alongside the Streamlit browser tab.
       - On other platforms: redirects stdout/stderr to DEVNULL.
    3. Poll /api/tags once per second for up to _STARTUP_TIMEOUT seconds.
    4. Return True if Ollama became available, False otherwise.

    Calling this multiple times is safe — the availability check runs first
    so a second call will see an already-running server and return True
    without launching a duplicate process.
    """
    # Already up — nothing to do.
    if is_ollama_available():
        return True

    # Launch ollama serve in the background.
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
    except FileNotFoundError:
        # ollama executable not found on PATH — not installed.
        return False
    except Exception:
        return False

    # Wait until the server becomes reachable.
    for _ in range(_STARTUP_TIMEOUT):
        time.sleep(1)
        if is_ollama_available():
            return True

    return False


# ── Availability Check ────────────────────────────────────────────────────────

def is_ollama_available() -> bool:
    """Return True if the local Ollama server is reachable."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Context Builder ───────────────────────────────────────────────────────────

def build_machine_context(machine) -> dict:
    """
    Build a structured context dict from a single machine row (pd.Series).
    Used to pass consistent context to both report generation and chat.
    """
    from utils.health import compute_health_score, compute_failure_probability

    score, category, color = compute_health_score(machine)
    has_failed = bool(int(machine.get("Machine failure", 0)) == 1)

    failure_modes = []
    mode_map = {
        "TWF": "Tool Wear Failure",
        "HDF": "Heat Dissipation Failure",
        "PWF": "Power Failure",
        "OSF": "Overstrain Failure",
        "RNF": "Random Failure",
    }
    for col, label in mode_map.items():
        if machine.get(col, 0) == 1:
            failure_modes.append(label)

    fp = compute_failure_probability(machine, score)

    return {
        "product_id":        machine["Product ID"],
        "machine_type":      {"L": "Low", "M": "Medium", "H": "High"}.get(machine["Type"], machine["Type"]),
        "type_code":         machine["Type"],
        "air_temp":          float(machine["Air temperature [K]"]),
        "proc_temp":         float(machine["Process temperature [K]"]),
        "rpm":               float(machine["Rotational speed [rpm]"]),
        "torque":            float(machine["Torque [Nm]"]),
        "tool_wear":         float(machine["Tool wear [min]"]),
        "has_failed":        has_failed,
        "failure_modes":     failure_modes,
        "health_score":      score,
        "health_category":   category,
        "failure_probability": fp,
    }


# ── Internal Prompt Formatters ────────────────────────────────────────────────

def _format_context_block(ctx: dict) -> str:
    """Format machine context as a structured text block for prompts."""
    failure_str = (
        f"FAILED — Active failure modes: {', '.join(ctx['failure_modes']) if ctx['failure_modes'] else 'Unknown'}"
        if ctx["has_failed"]
        else "Healthy — No failure detected"
    )
    return f"""
MACHINE INFORMATION:
  Product ID   : {ctx['product_id']}
  Machine Type : {ctx['machine_type']} Grade ({ctx['type_code']})

CURRENT SENSOR READINGS:
  Air Temperature    : {ctx['air_temp']:.1f} K
  Process Temperature: {ctx['proc_temp']:.1f} K
  Rotational Speed   : {ctx['rpm']:.0f} RPM
  Torque             : {ctx['torque']:.1f} Nm
  Tool Wear          : {ctx['tool_wear']:.0f} min

FAILURE PREDICTION:
  Status             : {failure_str}
  Health Score       : {ctx['health_score']}/100 ({ctx['health_category']})
  Failure Probability: {ctx['failure_probability']}%
""".strip()


def _stream_ollama(prompt: str) -> Iterator[str]:
    """
    Core streaming function — POSTs to Ollama and yields tokens one at a time.
    Raises on connection errors.
    """
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
    }
    with requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json=payload,
        stream=True,
        timeout=_STREAM_TIMEOUT,
    ) as resp:
        resp.raise_for_status()
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            try:
                data = json.loads(raw_line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                continue


# ── Public API ────────────────────────────────────────────────────────────────

def generate_report(context: dict) -> Iterator[str]:
    """
    Stream a professional maintenance report for the given machine context.
    Yields tokens as they arrive from Ollama.
    """
    ctx_block = _format_context_block(context)

    prompt = f"""You are a senior industrial maintenance engineer with 20+ years of experience in predictive maintenance systems.

{ctx_block}

Generate a comprehensive, professional maintenance report. Structure it with the following clearly labelled sections:

1. EXECUTIVE SUMMARY
2. CURRENT MACHINE CONDITION
3. FAILURE ANALYSIS (describe active failures) OR OPERATIONAL STATUS (if healthy)
4. ROOT CAUSE ANALYSIS
5. RECOMMENDED MAINTENANCE ACTIONS (prioritized numbered list)
6. PREVENTIVE MEASURES
7. PRIORITY LEVEL: Critical / High / Medium / Low (state clearly)
8. ESTIMATED DOWNTIME (if maintenance required, else "No downtime required")
9. RECOMMENDED SPARE PARTS
10. CONCLUSION AND NEXT STEPS

Guidelines:
- Write in a professional, technical, and concise manner
- Be specific — reference the actual sensor values when relevant
- Focus EXCLUSIVELY on machine {context['product_id']} and the data provided above
- Use clear section headers followed by the content
- Provide actionable recommendations with timeframes
"""
    yield from _stream_ollama(prompt)


def chat(
    context: dict,
    report: str,
    history: list,
    question: str,
) -> Iterator[str]:
    """
    Stream a context-aware chat response.
    Includes: machine context, generated report, conversation history, and the new question.
    Yields tokens as they arrive from Ollama.
    """
    ctx_block = _format_context_block(context)

    # Include the last 8 messages (4 exchanges) for context window efficiency
    history_block = ""
    if history:
        history_block = "\nCONVERSATION HISTORY:\n"
        for msg in history[-8:]:
            role = "Engineer" if msg["role"] == "user" else "AI Assistant"
            history_block += f"{role}: {msg['content']}\n"

    report_block = ""
    if report:
        # Truncate very long reports to first 1500 chars to save context window
        truncated = report[:1800] + "..." if len(report) > 1800 else report
        report_block = f"\nGENERATED MAINTENANCE REPORT (summary):\n{truncated}\n"

    prompt = f"""You are a senior industrial maintenance engineer specialising in predictive maintenance.

{ctx_block}
{report_block}
{history_block}

STRICT INSTRUCTIONS:
- You are advising about machine {context['product_id']} ONLY
- Answer ONLY based on the machine data provided above
- Be professional, technical, and concise
- Reference specific sensor values when relevant
- Do NOT answer questions unrelated to this machine or predictive maintenance

Engineer's Question: {question}

Answer:"""

    yield from _stream_ollama(prompt)
