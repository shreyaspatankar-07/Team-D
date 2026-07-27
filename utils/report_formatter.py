"""
utils/report_formatter.py — AI report formatting, metadata, and export (MD + PDF).

PDF export uses aggressive Unicode-to-ASCII sanitisation so that fpdf2's
built-in Helvetica font never throws an encoding exception.
"""

from datetime import datetime
import unicodedata

OLLAMA_MODEL         = "llama3.2"
OLLAMA_MODEL_DISPLAY = "Llama 3.2 (Local)"


# ── Unicode Sanitiser (for PDF) ───────────────────────────────────────────────

# Explicit character substitutions (covers most LLM output quirks)
_UNICODE_MAP = {
    "\u2014": "-",    # em-dash
    "\u2013": "-",    # en-dash
    "\u2012": "-",    # figure dash
    "\u2010": "-",    # hyphen
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201a": ",",    # single low quote
    "\u201b": "'",    # single high reversed
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u201e": '"',    # double low quote
    "\u201f": '"',    # double high reversed
    "\u2022": "*",    # bullet
    "\u2023": ">",    # triangular bullet
    "\u2024": ".",    # one dot leader
    "\u2025": "..",   # two dot leader
    "\u2026": "...",  # ellipsis
    "\u2027": ".",    # hyphenation point
    "\u2028": "\n",   # line separator
    "\u2029": "\n\n", # paragraph separator
    "\u2032": "'",    # prime
    "\u2033": '"',    # double prime
    "\u2039": "<",    # single left angle quote
    "\u203a": ">",    # single right angle quote
    "\u2122": "(TM)", # trademark
    "\u00ae": "(R)",  # registered trademark
    "\u00a9": "(c)",  # copyright
    "\u00b0": " deg", # degree
    "\u00b1": "+/-",  # plus-minus
    "\u00b2": "^2",   # superscript 2
    "\u00b3": "^3",   # superscript 3
    "\u00d7": "x",    # multiplication sign
    "\u00f7": "/",    # division sign
    "\u2190": "<-",   # left arrow
    "\u2192": "->",   # right arrow
    "\u2191": "^",    # up arrow
    "\u2193": "v",    # down arrow
    "\u2260": "!=",   # not equal
    "\u2248": "~=",   # approximately equal
    "\u2265": ">=",   # greater-than or equal
    "\u2264": "<=",   # less-than or equal
    "\u2212": "-",    # minus sign
    "\u221e": "inf",  # infinity
    "\u2713": "v",    # check mark
    "\u2714": "v",    # heavy check mark
    "\u2717": "x",    # ballot x
    "\u2718": "x",    # heavy ballot x
    "\u25cf": "*",    # black circle
    "\u25cb": "o",    # white circle
    "\u25a0": "[X]",  # black square
    "\u25a1": "[ ]",  # white square
    "\u2665": "<3",   # heart
    "\u2764": "<3",   # heavy heart
    "\u00a0": " ",    # non-breaking space
    "\u00ad": "",     # soft hyphen (remove)
}


def _safe_str(text: str) -> str:
    """
    Convert a string to a safe Latin-1 string for fpdf2 / Helvetica.

    Steps:
    1. Apply explicit character map for known LLM output characters.
    2. Use unicodedata NFKD normalisation to decompose accented chars.
    3. Encode to latin-1 with 'replace' as final fallback (unknown → '?').
    """
    if not text:
        return ""
    # Step 1: explicit substitutions
    for char, replacement in _UNICODE_MAP.items():
        text = text.replace(char, replacement)
    # Step 2: strip emoji / remove non-printable control chars
    # (keep newlines, tabs, and printable ASCII)
    cleaned = []
    for char in text:
        cp = ord(char)
        if cp < 32 and char not in ("\n", "\t", "\r"):
            continue  # skip control characters
        if cp > 127:
            # Try NFKD decomposition (handles é → e + combining accent)
            norm = unicodedata.normalize("NFKD", char)
            ascii_chars = norm.encode("ascii", errors="ignore").decode("ascii")
            if ascii_chars:
                cleaned.append(ascii_chars)
            # else: silently skip unrepresentable character
        else:
            cleaned.append(char)
    return "".join(cleaned)


# ── Metadata ──────────────────────────────────────────────────────────────────

def get_report_metadata(machine_id: str) -> dict:
    """Return metadata dict for a freshly generated report."""
    return {
        "machine_id": machine_id,
        "model":      OLLAMA_MODEL_DISPLAY,
        "timestamp":  datetime.now(),
        "ts_display": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def render_report_metadata_html(meta: dict) -> str:
    """Render the report metadata bar as HTML (inline styles only)."""
    mid   = meta.get("machine_id", "N/A")
    model = meta.get("model", "N/A")
    ts    = meta.get("ts_display", "N/A")
    return f"""
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;
                padding:10px 16px; margin-bottom:14px; font-size:0.76rem; color:#64748b;">
        <strong style="color:#1e293b;">Machine ID:</strong> {mid}
        &nbsp;<span style="color:#cbd5e1;">|</span>&nbsp;
        <strong style="color:#1e293b;">Model:</strong> {model}
        &nbsp;<span style="color:#cbd5e1;">|</span>&nbsp;
        <strong style="color:#1e293b;">Generated:</strong> {ts}
    </div>
    """


# ── Markdown Export ───────────────────────────────────────────────────────────

def build_markdown_report(report_text: str, meta: dict, context: dict) -> str:
    """Build a complete Markdown document for download."""
    header = f"""# Maintenance Report — {meta.get('machine_id','N/A')}

---

**Machine ID:** {meta.get('machine_id','N/A')}  
**Machine Type:** {context.get('machine_type','N/A')} Grade ({context.get('type_code','N/A')})  
**Generated:** {meta.get('ts_display','N/A')}  
**AI Model:** {meta.get('model','N/A')}  

---

## Sensor Readings

| Sensor | Value |
|--------|-------|
| Air Temperature | {context.get('air_temp','N/A')} K |
| Process Temperature | {context.get('proc_temp','N/A')} K |
| Rotational Speed | {context.get('rpm','N/A')} RPM |
| Torque | {context.get('torque','N/A')} Nm |
| Tool Wear | {context.get('tool_wear','N/A')} min |

## Prediction

- **Status:** {'FAILED' if context.get('has_failed') else 'Healthy'}
- **Health Score:** {context.get('health_score','N/A')} / 100 ({context.get('health_category','N/A')})
- **Failure Probability:** {context.get('failure_probability','N/A')}%

---

## AI-Generated Report

"""
    footer = f"""

---

*Report generated by Machine Failure Analysis Platform using {meta.get('model','N/A')}*  
*{meta.get('ts_display','N/A')}*
"""
    return header + report_text + footer


# ── PDF Export ────────────────────────────────────────────────────────────────

def build_pdf_report(report_text: str, meta: dict, context: dict) -> bytes | None:
    """
    Build a PDF using fpdf2.
    All text is passed through _safe_str() to guarantee Latin-1 compatibility.
    Returns PDF bytes, or None if fpdf2 is not installed or generation fails.
    """
    try:
        from fpdf import FPDF

        machine_id_safe = _safe_str(meta.get("machine_id", "Unknown"))
        ts_safe         = _safe_str(meta.get("ts_display", ""))
        model_safe      = _safe_str(meta.get("model", OLLAMA_MODEL_DISPLAY))

        class ReportPDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 14)
                self.set_text_color(30, 58, 95)
                self.cell(0, 10, f"Maintenance Report - {machine_id_safe}", align="L")
                self.ln(4)
                self.set_font("Helvetica", "", 9)
                self.set_text_color(100, 116, 139)
                self.cell(0, 6, f"Generated: {ts_safe}  |  Model: {model_safe}", align="L")
                self.ln(8)
                self.set_draw_color(226, 232, 240)
                self.set_line_width(0.4)
                self.line(10, self.get_y(), 200, self.get_y())
                self.ln(4)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f"Machine Failure Analysis Platform  |  Page {self.page_no()}", align="C")

        pdf = ReportPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        def _section(title: str) -> None:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 8, _safe_str(title), ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 41, 59)

        # Machine Information
        _section("Machine Information")
        info_lines = [
            f"Machine ID: {meta.get('machine_id','N/A')}",
            f"Machine Type: {context.get('machine_type','N/A')} Grade ({context.get('type_code','N/A')})",
            f"Status: {'FAILED' if context.get('has_failed') else 'Healthy'}",
            f"Health Score: {context.get('health_score','N/A')} / 100 ({context.get('health_category','N/A')})",
            f"Failure Probability: {context.get('failure_probability','N/A')}%",
        ]
        for line in info_lines:
            pdf.cell(0, 6, _safe_str(line), ln=True)
        pdf.ln(4)

        # Sensor Readings
        _section("Sensor Readings")
        sensor_lines = [
            f"Air Temperature: {context.get('air_temp','N/A')} K",
            f"Process Temperature: {context.get('proc_temp','N/A')} K",
            f"Rotational Speed: {context.get('rpm','N/A')} RPM",
            f"Torque: {context.get('torque','N/A')} Nm",
            f"Tool Wear: {context.get('tool_wear','N/A')} min",
        ]
        for line in sensor_lines:
            pdf.cell(0, 6, _safe_str(line), ln=True)
        pdf.ln(4)

        # AI Report
        _section("AI-Generated Maintenance Report")
        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)

        for para in report_text.split("\n"):
            safe_para = _safe_str(para.strip())
            if not safe_para:
                pdf.ln(3)
                continue

            is_header = (
                safe_para.isupper()
                or (len(safe_para) > 2 and safe_para[0].isdigit() and safe_para[1] == ".")
                or safe_para.startswith("##")
                or safe_para.startswith("#")
            )
            clean = _safe_str(safe_para.lstrip("#").strip())
            if not clean:
                continue

            if is_header:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 58, 95)
                pdf.multi_cell(0, 7, clean)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(30, 41, 59)
            else:
                pdf.multi_cell(0, 6, clean)

        return bytes(pdf.output())

    except ImportError:
        return None
    except Exception:
        # Any encoding or layout error: return None rather than crashing
        return None
