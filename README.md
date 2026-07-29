# Agentic Facility Operations

A Streamlit application for exploring the AI4I 2020 predictive-maintenance dataset, reviewing machine failures, and managing maintenance work orders.

## Getting Started

Install the dependencies and start the application:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The application uses `ai4i2020.csv` for machine data and stores work orders locally in `maintenance_work_orders.db`.

## Modules

### Module 1: EDA

Provides exploratory data analysis for the loaded dataset. It displays the dataset preview, column and row metrics, missing-value checks, descriptive statistics, correlation analysis, a correlation heatmap, and selectable histograms.

### Module 2: Dashboard

Summarizes machine health and failure patterns. KPI cards show the selected population, healthy machines, failures, and average tool wear. Interactive charts show failure trends, failure-mode distribution, machine types, failure rates, and RPM/tool-wear relationships.

### Module 3: Machine Explorer

Allows users to search for a Product ID or select a machine from the filtered dataset. It presents the machine's health assessment, sensor readings, failure modes, technical indicators, and maintenance focus.

### Module 4: AI Maintenance Assistant

Uses the selected machine record to provide a quick assessment, a streamed maintenance report, and conversational answers. The assistant uses a locally available Ollama model when Ollama is running; the application remains usable for non-AI features when it is unavailable.

The assistant can also create a work order for machines with a recorded failure. Each machine can have only one active work order.

### Module 5 & 6: Work Order Management

Provides a persistent work-order register backed by SQLite. Users can:

- View all work orders.
- Search by order ID, Product ID, failure reason, or recommended action.
- Filter by status and priority.
- Update status and priority.
- Delete an order after confirmation.
- Review KPI cards for total, open, in-progress, closed, and critical orders.
- Export the current results as JSON or CSV.

New work orders start as `Open` with `High` priority and include the failure reason, recommended action, creation timestamp, and update timestamp.

## Sidebar Filters

The global filters limit the machine dataset used by Modules 1-4. Module 5 & 6 manages the persistent work-order database independently, so it remains available even when no machines match the dataset filters.

## Project Files

- `app.py` - Streamlit user interface and module rendering.
- `work_orders.py` - SQLite work-order creation, search, filtering, updates, and deletion.
- `ai.py` - Ollama communication and maintenance-assistant prompts.
- `ai4i2020.csv` - Source predictive-maintenance dataset.
- `maintenance_work_orders.db` - Local persistent work-order database.
- `requirements.txt` - Python dependencies.
