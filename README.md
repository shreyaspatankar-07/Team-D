<<<<<<< HEAD
# Machine Failure Analysis Platform

An interactive **Predictive Maintenance** web application built on the **AI4I 2020 dataset**, featuring a multi-page Streamlit dashboard, AI-powered analysis, automated work order management, and session-based authentication.

---

## Features

### 📊 Dashboard
- KPI cards: total records, machine types, failure rate, healthy machines
- Overview charts: failure distribution, failure mode breakdown, machine type composition

### 📈 Data Analytics
- Sensor parameter distributions (temperature, torque, tool wear, RPM)
- Pearson correlation heatmap
- Failure rate by machine type and wear range
- Sidebar filters: Machine Type (L/M/H) and Failure Status

### 🔍 Machine Explorer
- Per-machine drill-down with full sensor history
- Failure timeline and condition trend charts
- Health score and risk assessment per machine

### 🤖 AI Assistant
- Natural language Q&A powered by a locally running Ollama LLM
- Context-aware responses grounded in filtered dataset state
- Persistent per-session chat history

### 🔧 Work Order Creation
- Create maintenance work orders tied to specific machines and failure types
- Stored in a local SQLite database (`work_orders.db`)

### 📋 Work Order Management
- View, update status, and manage all open/closed work orders
- Filter and search by machine, status, or failure type

### 🛡️ Preventive Maintenance
- AI-generated maintenance schedules per machine
- Risk scoring and recommended maintenance intervals
- PDF export of preventive maintenance reports

### 🔐 Authentication
- Session-based login and logout
- Two built-in roles: **Admin** and **Employee**
- Credentials stored and verified against the SQLite database
- Login page hidden from sidebar; dashboard fully gated behind auth

---

## Technologies

| Layer         | Technology                                      |
|---------------|-------------------------------------------------|
| Frontend      | Streamlit ≥ 1.31, Plotly, custom CSS            |
| Data          | Pandas, NumPy, AI4I 2020 CSV (10,000 records)   |
| AI / LLM      | Ollama (local, auto-start), `requests`          |
| Database      | SQLite via Python `sqlite3` (`work_orders.db`)  |
| PDF Export    | fpdf2                                           |
| Visualisation | Plotly, Matplotlib, Seaborn                     |
| Notebook      | Jupyter, Matplotlib, Seaborn                    |

---

## Project Structure

```
Machine Failure Analysis/
│
├── app.py                          # Main entry point — routing & sidebar
├── requirements.txt
├── ai4i2020.csv                    # AI4I 2020 Predictive Maintenance Dataset
├── work_orders.db                  # SQLite database (auto-created on first run)
├── README.md
│
├── pages/
│   ├── login.py                    # Login page & auth gate
│   ├── dashboard.py                # Overview KPIs and charts
│   ├── analytics.py                # In-depth data analytics
│   ├── machine_explorer.py         # Per-machine drill-down
│   ├── ai_assistant.py             # LLM-powered chat assistant
│   ├── work_order_creation.py      # Create new work orders
│   ├── work_order_management.py    # Manage existing work orders
│   └── preventive_maintenance.py   # AI maintenance schedules
│
├── utils/
│   ├── auth.py                     # Login/logout, session state, credentials
│   ├── data.py                     # Data loading and filtering helpers
│   ├── db.py                       # SQLite schema init and CRUD helpers
│   ├── charts.py                   # Reusable Plotly chart builders
│   ├── styles.py                   # Global CSS injection
│   ├── health.py                   # Machine health scoring
│   ├── ollama_service.py           # Ollama auto-start and LLM calls
│   ├── pm_ai.py                    # Preventive maintenance AI logic
│   ├── report_formatter.py         # PDF report generation
│   └── timeline.py                 # Failure timeline helpers
│
└── notebooks/
    └── EDA_AI4I_Analysis.ipynb     # Exploratory data analysis notebook
```

---

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/subal-v-r/Machine-Failure-Analysis.git
cd "Machine Failure Analysis"

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

### AI Assistant (optional)
The AI Assistant requires [Ollama](https://ollama.com) installed locally. The application will attempt to start Ollama automatically. If it cannot, a warning is shown in the sidebar and the assistant feature is disabled.

---

## Running the Application

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

### Default Credentials

| Role     | Username | Password  |
|----------|----------|-----------|
| Admin    | `admin`  | `admin` |
| Employee | `employee`   | `employee`  |

---

## Dataset

**AI4I 2020 Predictive Maintenance Dataset**
- Source: UCI Machine Learning Repository
- Records: 10,000 simulated industrial machine entries
- Features: 14 (air temperature, process temperature, RPM, torque, tool wear + 5 failure mode flags)
- Failure rate: ~3.4%
- Author: Stephan Matzka, HTW Berlin (2020)

---

## Jupyter Notebook (EDA)

```bash
jupyter notebook notebooks/EDA_AI4I_Analysis.ipynb
```

Run all cells top-to-bottom for the full exploratory data analysis with statistical observations and visualisations.
=======
# Team-D
>>>>>>> 52cd0e0 (Initial commit)
