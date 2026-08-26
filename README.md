# 🤖 Agentic AI for Smart Facility Operations and Optimization

An AI-powered **Facility Maintenance and Predictive Maintenance Management Platform** built with Python and Streamlit. It combines exploratory data analysis, predictive maintenance analytics, machine monitoring, an AI maintenance assistant, work-order management, and preventive maintenance scheduling into a single interactive application — powered by a locally-hosted LLM via **Ollama**, with no external API dependency.

> 🎓 **This project was developed as part of the Infosys Springboard Internship Program.**

---

## 📌 Overview

The **Agentic FacilityOps AI Platform** helps organizations monitor machine health, identify potential failures, manage maintenance activities, and make data-driven maintenance decisions.

It simulates a real-world **Computerized Maintenance Management System (CMMS)** enhanced with agentic AI capabilities, using the **AI4I 2020 Predictive Maintenance Dataset** to monitor machine health, automatically flag failures, and trigger a local LLM to generate structured maintenance recommendations and reports — fully offline-capable via Ollama.

---

## ✨ Key Features

### 🔬 Exploratory Data Analysis
- Dataset overview and statistical summary
- Missing-value and duplicate-value detection
- Feature correlation heatmap
- Interactive data visualizations

### 📈 Predictive Maintenance Analytics (Dashboard)
- Real-time KPI cards (total/healthy/failed machines, avg RPM, torque, tool wear, temperature)
- Machine failure mode distribution
- Machine-type breakdown
- Tool-wear time analysis
- RPM vs Torque correlation
- Global filters by machine status and type

### 🔍 Machine Explorer
- Search machines by Product ID (dropdown or manual search)
- View individual machine live sensor telemetry
- Failure mode diagnostics (TWF, HDF, PWF, OSF, RNF)
- Auto-redirects Admins to the AI Maintenance Assistant when a failure is detected

### 🤖 AI Maintenance Assistant
- Generates structured diagnostic reports via a local LLM (Ollama)
- Auto-triggered on failure detection, or run on demand
- Structured output: Executive Summary, KPIs, Root Cause Analysis, Recommended Actions, Maintenance Schedule
- Auto-fills Work Order priority and maintenance type based on the AI report

### 🔧 Work Order Creation
- Create and store maintenance work orders
- Attach AI-generated diagnostic reports
- Assign technician, priority, maintenance type, and status
- SQLite database persistence

### 📋 Work Order Management
- Search, filter, and view all work orders
- Update work-order status
- Delete work orders (Admin only)
- Export work orders as **PDF** or **Word (.docx)** reports
- Visual report card with machine health gauge and live telemetry

### 🛡️ Preventive Maintenance Scheduler
- Configure maintenance frequency (Daily/Weekly/Monthly/Quarterly/Yearly)
- Assign technicians and maintenance checklists
- Track overdue and upcoming (7-day) maintenance
- Generate preventive work orders directly from a schedule
- AI-based recommended maintenance frequency and checklist generation

### 🔐 Authentication
- Role-based login (Admin / Technician)
- SHA-256 hashed credentials stored in SQLite
- Session-based access control
- Role-based module visibility (RBAC)

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────────┐
                    │        User / Admin      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Streamlit UI        │
                    │    HTML + CSS + Python   │
                    └────────────┬─────────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
             ▼                   ▼                   ▼
      ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
      │ Data        │    │ Maintenance  │    │ Work Order   │
      │ Analytics   │    │ Management   │    │ Management   │
      └──────┬──────┘    └──────┬───────┘    └──────┬───────┘
             │                   │                   │
             ▼                   ▼                   ▼
      ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
      │ Pandas      │    │ Preventive   │    │ SQLite       │
      │ NumPy       │    │ Maintenance  │    │ Database     │
      └──────┬──────┘    └──────┬───────┘    └──────────────┘
             │                   │
             └──────────┬────────┘
                        ▼
                ┌───────────────┐
                │ Ollama / LLM  │
                │ AI Assistant  │
                └───────────────┘
```

---

## 🧰 Technologies Used

| Layer | Technologies |
|---|---|
| Frontend / App Framework | Streamlit, HTML, CSS |
| Programming | Python |
| Data Handling | Pandas, NumPy |
| Visualization | Plotly (Express & Graph Objects), Matplotlib, Seaborn |
| AI / LLM | Ollama (local inference, e.g. `llama3.2:1b`) |
| Database | SQLite3 (local, file-based) |
| Document Generation | WeasyPrint / fpdf2 (PDF), python-docx (Word) |
| Auth | SHA-256 hashed credentials |
| Dataset | AI4I 2020 Predictive Maintenance Dataset |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
.
├── app.py              # Main Streamlit application (all logic & UI)
├── ai4i2020.csv         # Required dataset (not included — see below)
├── work_orders.db        # Auto-generated SQLite database (created on first run)
└── README.md
```

> The entire application logic — authentication, dashboard, machine explorer, AI assistant, work orders, and preventive maintenance — is implemented in a single `app.py` file for simplicity and easy deployment.

---

## ⚙️ Prerequisites

1. **Python 3.9+**
2. **Ollama** installed and running locally for AI features:
   ```bash
   # Install Ollama: https://ollama.com/download
   ollama serve
   ollama pull llama3.2:1b
   ```
3. **The AI4I 2020 dataset** (`ai4i2020.csv`), placed in the same directory as `app.py`. Download it from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).

---

## 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install streamlit pandas numpy plotly matplotlib seaborn requests weasyprint fpdf2 python-docx

# 4. Place the dataset
# Download ai4i2020.csv and place it in the project root folder

# 5. Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

> 💡 If WeasyPrint fails to install/run on your system (it has native OS dependencies), the app automatically falls back to `fpdf2` for PDF generation — no action needed.

---

## 🔑 Demo Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Technician | `david` | `tech123` |

> ⚠️ These are demo credentials seeded automatically into the local SQLite database on first run. **Change or remove them before any production deployment.**

---

## 🧭 Application Modules

| Module | Access | Description |
|---|---|---|
| **Dashboard** | All roles | Fleet-wide KPIs, failure mode distribution, tool wear analysis, RPM vs Torque correlation |
| **Data Analysis (EDA)** | Admin only | Dataset preview, statistical summary, feature correlation heatmap |
| **Machine Explorer** | All roles | Search/select individual machines, view live telemetry, auto-redirects Admins to AI Assistant on failure detection |
| **AI Maintenance Assistant** | Admin only | Generates a structured diagnostic report via a local LLM (Ollama) based on machine telemetry |
| **Work Order Creation** | Admin only | Create and store maintenance work orders, optionally attaching the AI-generated report |
| **Work Order Management** | All roles (filtered by technician for non-admins) | Search, filter, update status, delete, and export work orders as PDF/DOCX |
| **Preventive Maintenance Scheduler** | Admin only | Create recurring PM schedules, track overdue/upcoming tasks, and get AI-recommended maintenance frequencies |

---

## 🔄 Application Workflow

```text
User Login
    │
    ▼
Dashboard
    │
    ├──► Exploratory Data Analysis
    │
    ├──► Machine Explorer
    │
    ├──► AI Maintenance Assistant
    │
    ├──► Work Order Creation
    │
    ├──► Work Order Management
    │
    └──► Preventive Maintenance Scheduler
```

## 📈 Predictive Maintenance Workflow

```text
Machine Sensor Data → Data Preprocessing → Exploratory Data Analysis
        → Machine Failure Analysis → Machine Health Evaluation
        → AI Maintenance Recommendation → Maintenance Work Order
        → Work Order Management → Maintenance History
```

## 🔧 Work Order Lifecycle

```text
Create Work Order → Assign Technician → Set Priority & Schedule
        → Maintenance In Progress → Complete Maintenance
        → Update Status → Store Maintenance History
```

---

## 🤖 How the AI Integration Works

- The app sends a structured prompt to a **local Ollama server** (`http://localhost:11434/api/generate`) — no data leaves your machine.
- The default model is `llama3.2:1b`, but this can be changed in the UI to any locally pulled Ollama model.
- The **AI Maintenance Assistant** returns a plain-text structured report (Executive Summary, KPIs, Root Cause, Recommendations, Maintenance Schedule).
- The **AI Recommendations** tab (under PM Scheduler) requests strict JSON output to auto-populate recommended maintenance frequency and checklists.
- If Ollama is not running, the app displays clear connection-error messages and gracefully continues without blocking other features.

**Example questions the assistant effectively answers via its structured report:**
```text
Why might this machine be at risk of failure?
What maintenance should be performed on this machine?
What does high tool wear indicate?
What preventive maintenance should be scheduled?
```

---

## 🗄️ Database

SQLite stores all application data locally, without needing a separate database server:

- Users (with hashed passwords and roles)
- Work orders (with AI-generated reports attached)
- Preventive maintenance schedules
- Assigned technicians and maintenance checklists
- Maintenance status and history

---

## 📊 Dataset

The project uses the **AI4I 2020 Predictive Maintenance Dataset**, containing machine operating and failure-related information:

- Product ID & Type
- Air temperature / Process temperature
- Rotational speed (RPM)
- Torque
- Tool wear
- Machine failure flag & failure modes (TWF, HDF, PWF, OSF, RNF)

These parameters drive machine health scoring, failure detection, and AI-based diagnostics.

---

## 🔒 Security Notes

- Passwords are stored as **SHA-256 hashes**, never in plaintext.
- The SQLite database (`work_orders.db`) is generated locally and is **not included** in this repository — do not commit it, as it may contain hashed credentials and operational data.
- No external API keys are required; all AI inference is local via Ollama.
- Use `.gitignore` to prevent sensitive or unnecessary files (`work_orders.db`, `__pycache__/`, `venv/`) from being committed.

---

## 🚀 Future Scope

- Machine-learning-based failure prediction models
- Real-time IoT sensor integration
- Cloud database integration
- Email/SMS maintenance notifications
- Technician mobile application
- Maintenance cost prediction
- Digital twin integration
- Advanced autonomous AI agents for maintenance planning

---

## 🎯 Applications

- Manufacturing industries & industrial plants
- Production facility maintenance departments
- Equipment and facility management
- Industrial IoT environments
- Predictive maintenance research & demos

---

## 💡 Advantages

- Centralized maintenance management in a single lightweight app
- Interactive, real-time machine monitoring
- Data-driven maintenance decisions
- AI-powered diagnostics without external API costs
- Reduced manual maintenance planning
- Preventive maintenance scheduling with AI recommendations
- User-friendly Streamlit interface

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

## 🙋 Support

For issues or questions, please open an issue in this repository.
