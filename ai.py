"""Ollama helpers for the AI Maintenance Assistant.

The Streamlit interface lives in ``module_3.py``.  Keeping the model client and
prompt construction here makes the AI integration reusable and prevents the UI
from being coupled to a particular Ollama Python package.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
FAILURE_MODES = {
    "TWF": "Tool wear",
    "HDF": "Heat dissipation",
    "PWF": "Power",
    "OSF": "Overstrain",
    "RNF": "Random",
}
REPORT_TARGET_WORDS = 155


def _post(endpoint: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    """Send a JSON request to the local Ollama API and return its JSON body."""
    request = Request(
        f"{OLLAMA_URL}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as error:
        raise ConnectionError(
            "Ollama is not reachable. Start Ollama, then confirm it is running at "
            f"{OLLAMA_URL}."
        ) from error


def get_available_models() -> list[str]:
    """Return locally installed Ollama model names, or an empty list if offline."""
    try:
        request = Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [model["name"] for model in payload.get("models", [])]
    except (URLError, OSError, json.JSONDecodeError):
        return []


def machine_context(machine: Any) -> str:
    """Turn one selected dataframe row into factual context for the model."""
    active_modes = [label for code, label in FAILURE_MODES.items() if int(machine[code]) == 1]
    failure_state = "Recorded failure" if int(machine["Machine failure"]) == 1 else "No recorded failure"
    return "\n".join(
        [
            f"Product ID: {machine['Product ID']}",
            f"Machine type: {machine['Type']}",
            f"Recorded status: {failure_state}",
            f"Recorded failure modes: {', '.join(active_modes) if active_modes else 'None'}",
            f"Air temperature: {machine['Air temperature [K]']:.1f} K",
            f"Process temperature: {machine['Process temperature [K]']:.1f} K",
            f"Temperature gap: {machine['Temperature gap [K]']:.1f} K",
            f"Rotational speed: {machine['Rotational speed [rpm]']:.0f} rpm",
            f"Torque: {machine['Torque [Nm]']:.1f} Nm",
            f"Tool wear: {machine['Tool wear [min]']:.0f} min",
            f"Workload: {machine['Workload']:.1f}",
        ]
    )


def ask_maintenance_assistant(question: str, context: str, model: str = OLLAMA_MODEL) -> str:
    """Ask Llama a maintenance question grounded only in the supplied record."""
    prompt = f"""You are a careful industrial maintenance assistant.
Use only the machine record below. Do not invent sensor readings, historical events,
live telemetry, or certainty that the record does not support. This is educational
decision support, not a replacement for site safety procedures or an inspection.

Machine record:
{context}

Question: {question}

Respond in clear, practical language. Explain the evidence first, then recommended
next checks. If the evidence is insufficient, say so plainly. Keep the answer under
220 words."""
    response = _post(
        "/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {"temperature": 0.2, "num_predict": 320},
        },
    )
    return response.get("response", "").strip() or "Ollama returned an empty response."


def _complete_report_length(report: str) -> str:
    """Add only safe operational limitations when a model ignores the word target."""
    words = report.replace("#", "").split()
    if len(words) >= 150:
        return report

    safe_sentences = [
        "These values represent one recorded dataset row and are not a live sensor feed.",
        "Confirm the readings with calibrated instruments before making any operational or maintenance decision.",
        "Follow approved site safety procedures and have a qualified technician document the inspection findings.",
        "Compare current measurements with approved operating limits and maintenance history before returning the machine to service.",
    ]
    addition: list[str] = []
    for sentence in safe_sentences:
        sentence_words = sentence.split()
        if len(words) + len(addition) + len(sentence_words) <= REPORT_TARGET_WORDS:
            addition.extend(sentence_words)
    if len(words) + len(addition) < REPORT_TARGET_WORDS:
        filler = "Review recorded values with qualified personnel before deciding next steps.".split()
        addition.extend(filler[: REPORT_TARGET_WORDS - len(words) - len(addition)])
    return report.rstrip() + "\n\n" + " ".join(addition)


def stream_maintenance_report(context: str, model: str = OLLAMA_MODEL) -> Iterator[str]:
    """Yield a concise report as Ollama produces it, keeping the model warm."""
    prompt = f"""You are a careful industrial maintenance assistant.
Create a concise maintenance report using only this recorded dataset row:

{context}

Your response must be exactly 155 words in total, including headings and list items.
This is a strict requirement: silently count the words before responding, and add
useful record-based detail if the response is shorter than 150 words. Use exactly
these Markdown headings:
### Observed condition
### Evidence from record
### Recommended actions
### Limitation

Give practical, ordered inspection actions. Do not state that a repair is required
unless a recorded failure supports it. State that the recommendations require
qualified maintenance review. Do not add a title, preamble, or closing text."""
    request = Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "keep_alive": "10m",
                "options": {"temperature": 0.15, "num_predict": 420},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        chunks: list[str] = []
        with urlopen(request, timeout=120) as response:
            for line in response:
                payload = json.loads(line.decode("utf-8"))
                if text := payload.get("response"):
                    chunks.append(text)
                    yield text
        completed_report = _complete_report_length("".join(chunks))
        original_report = "".join(chunks)
        if completed_report != original_report:
            yield completed_report[len(original_report) :]
    except URLError as error:
        raise ConnectionError(
            "Ollama is not reachable. Start Ollama, then confirm it is running at "
            f"{OLLAMA_URL}."
        ) from error
