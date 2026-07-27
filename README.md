# AI4I Machine Failure — EDA Dashboard

An exploratory data analysis project for the **AI4I 2020 Predictive Maintenance Dataset**
built as a university academic submission.

---

## Project Overview

This project analyses 10,000 simulated industrial machine records to understand what
process conditions lead to machine failures. It consists of two independent deliverables:

1. **Jupyter Notebook** — complete EDA with visualizations and written observations.
2. **Streamlit Web Application** — interactive dashboard with sidebar filtering, Plotly
   charts, descriptive statistics, and a Pearson correlation heatmap.

---

## Folder Structure

```
Machine Failure Analysis/
│
├── app.py                  # Streamlit dashboard (run with: streamlit run app.py)
├── requirements.txt        # Python dependencies
├── ai4i2020.csv            # Dataset
├── README.md
│
└── notebooks/
    └── EDA_AI4I_Analysis.ipynb   # Jupyter EDA notebook
```

---

## Technologies Used

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Dashboard  | Python 3.x, Streamlit, Pandas, NumPy   |
| Charts     | Plotly (go.Figure, go.Pie, go.Bar, go.Heatmap) |
| Notebook   | Jupyter, Matplotlib, Seaborn            |

---

## Installation

```bash
# 1. Clone / download the project folder
# 2. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Project

### Web Application

```bash
streamlit run app.py
```

Then open your browser at: **http://localhost:8501**

### Jupyter Notebook

```bash
jupyter notebook notebooks/EDA_AI4I_Analysis.ipynb
```

Run all cells from top to bottom — no manual intervention required.

---

## Features

- **Dashboard** — KPI cards (total records, features, failures, machine types) + overview charts
- **Dataset Preview** — first 10 rows with shape dimensions
- **Descriptive Statistics** — formatted summary table (count, mean, std, quartiles)
- **Correlation Heatmap** — colour-coded Pearson correlation matrix (red–white–blue)
- **Machine Failure Analysis** — failure distribution + failure rate by machine type
- **Machine Type Analysis** — type composition bar chart
- **RPM Analysis** — rotational speed frequency histogram
- **Tool Wear Analysis** — wear histogram + colour-coded failure rate by wear range
- **Sidebar Filters** — filter all charts by Machine Type (L/M/H) and Failure Status

---

## Dataset

**AI4I 2020 Predictive Maintenance Dataset**
- Source: UCI Machine Learning Repository
- Records: 10,000
- Features: 14 (including 5 failure mode flags)
- Failure rate: ~3.4%

Author: Stephan Matzka, HTW Berlin (2020)
