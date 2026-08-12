# Agentic AI for Smart Facility Operations and Optimization Group 2

## Project Documentation

**Programme:** Infosys Springboard Internship  
**Project title:** Agentic AI for Smart Facility Operations and Optimization Group 2  
**Application name:** Agentic Facility Operations

## 1. Project overview

Agentic Facility Operations is a local Streamlit application that combines machine-failure exploration with maintenance operations management. It uses the bundled AI4I 2020 predictive-maintenance dataset to help users inspect historical machine records, review failure patterns, assess individual machines, obtain local AI-assisted maintenance guidance, and manage corrective and preventive maintenance work orders.

The application is a prototype for facility-operations decision support. The machine values displayed in the interface are historical dataset records, not live sensor telemetry. The repository does not include integrations with physical machines, enterprise CMMS platforms, ERP systems, or external production databases.

## 2. Business problem addressed

Maintenance teams need to turn equipment-condition information into organized maintenance action. Historical machine data alone can be difficult to use operationally when users must separately identify failures, interpret likely causes, create maintenance tickets, track status, and plan recurring work.

This project brings these activities into one local application. It supports the following workflow:

1. Explore historical machine-failure data and failure distributions.
2. Filter the population by machine type, status, tool wear, and, in Machine Explorer, failure mode.
3. Inspect a selected machine's recorded sensor values and failure flags.
4. Generate record-grounded maintenance guidance through a locally available Ollama model.
5. Create and manage corrective work orders for recorded failures.
6. Configure recurring preventive-maintenance schedules, checklists, and maintenance completion history.

## 3. Objectives

- Provide exploratory data analysis for the machine-maintenance dataset.
- Present machine health and failure patterns through an interactive dashboard.
- Enable users to retrieve and inspect individual machine records by Product ID.
- Translate recorded failure modes into practical, rule-based recommended inspection actions.
- Provide local AI-assisted maintenance responses grounded in the selected dataset record.
- Persist corrective and preventive work-order information in a local database.
- Support recurring preventive-maintenance scheduling and checklist-controlled completion.

## 4. Technology stack

| Layer | Technology used |
|---|---|
| Programming language | Python |
| Web application framework | Streamlit |
| Data analysis | pandas, NumPy |
| Visualization | Plotly and Plotly Express |
| Local persistence | SQLite through Python's `sqlite3` module |
| AI service | Local Ollama HTTP API |
| Default AI model setting | `llama3.2:latest` |
| Authentication | Custom local authentication with salted PBKDF2-HMAC-SHA256 password hashing |
| Data source format | CSV |
| Export formats | CSV, JSON, Markdown |
| Version control | Git, with a GitHub remote configured |

The pinned dependencies are listed in `requirements.txt`. The application directly uses Streamlit, pandas, Plotly, SQLite, and Python standard-library modules for security, dates, and HTTP communication.

## 5. System architecture

```text
AI4I CSV dataset
       |
       v
Streamlit application (app.py)
       |
       +--> EDA, dashboard, filters, and Machine Explorer
       |
       +--> AI Maintenance Assistant --> Local Ollama API
       |
       +--> Work-order and preventive-maintenance functions --> SQLite database
       |
       +--> Login and registration --> SQLite authentication database
```

The Streamlit application is the user interface and orchestration layer. It loads the CSV data with pandas, renders interactive Plotly visualizations, invokes local SQLite functions for persistence, and sends factual selected-record context to Ollama for AI responses.

## 6. Dataset details

The repository contains `ai4i2020.csv`, identified in the project README as the AI4I 2020 predictive-maintenance dataset. The repository does not provide the original publisher, license, collection methodology, or source URL; therefore, those details are not claimed here.

### Verified dataset profile

| Metric | Value |
|---|---:|
| Rows | 10,000 |
| Original columns | 14 |
| Missing values | 0 |
| Unique Product IDs | 10,000 |
| UDI range | 1 to 10,000 |
| Recorded machine failures | 339 |
| Recorded failure rate | 3.39% |

### Source fields

- `UDI`
- `Product ID`
- `Type`
- `Air temperature [K]`
- `Process temperature [K]`
- `Rotational speed [rpm]`
- `Torque [Nm]`
- `Tool wear [min]`
- `Machine failure`
- `TWF` — tool wear failure
- `HDF` — heat dissipation failure
- `PWF` — power failure
- `OSF` — overstrain failure
- `RNF` — random failure

### Verified machine-type distribution

| Type | Records |
|---|---:|
| L | 6,000 |
| M | 2,997 |
| H | 1,003 |

### Verified recorded failure-mode counts

| Failure mode | Count |
|---|---:|
| Heat dissipation (`HDF`) | 115 |
| Overstrain (`OSF`) | 98 |
| Power (`PWF`) | 95 |
| Tool wear (`TWF`) | 46 |
| Random (`RNF`) | 19 |

The five failure-mode counts total 373, while the dataset contains 339 failed machine records. This indicates that some records have multiple failure-mode flags.

## 7. Data preparation and feature engineering

The application does not perform imputation, outlier removal, scaling, encoding, or train/test splitting. The bundled data contains no missing values.

When loading the CSV, the application creates the following derived fields:

| Derived field | Calculation / purpose |
|---|---|
| `Status` | Maps `Machine failure` from `0`/`1` to `Healthy`/`Failed`. |
| `Temperature gap [K]` | `Process temperature [K] - Air temperature [K]`. |
| `Workload` | `Rotational speed [rpm] * Torque [Nm] / 1000`. |

Interactive filtering is then applied by machine type, status, and tool-wear range. Machine Explorer also supports failure-mode filtering.

## 8. Application modules and functionality

### Module 1: Exploratory Data Analysis

The EDA module provides:

- a preview of the first 25 filtered records;
- row, column, missing-value, and numeric-field KPI cards;
- a per-column null-value table;
- descriptive statistics using `describe(include="all")`;
- a selectable numeric correlation heatmap;
- ranked correlations with `Machine failure`;
- selectable status-coloured histograms.

The correlation analysis is descriptive. The project does not run inferential statistical tests or make causal claims.

### Module 2: Machine Failure Dashboard

The dashboard provides KPI cards for:

- selected machines;
- healthy machines;
- recorded failures;
- average tool wear;
- the machine type with the highest displayed failure rate.

Interactive Plotly visualizations include:

- a failure-rate line chart across up to 12 quantile-based `UDI` segments;
- a healthy-versus-failed donut chart;
- a horizontal failure-mode bar chart;
- an RPM-versus-torque scatter plot where marker size represents tool wear and colour represents status;
- a machine-type distribution chart;
- a failure-rate-by-machine-type chart.

The chart labelled as a failure-rate trend uses `UDI` quantile segments. The repository does not establish that `UDI` represents time or actual production periods.

### Module 3: Machine Explorer

Users can search by Product ID or select a machine from the currently filtered group. The module shows:

- Product ID, type, and UDI;
- a rule-based health assessment;
- five sensor gauges for air temperature, process temperature, rotational speed, torque, and tool wear;
- recorded failure-mode indicators;
- a visible note that values are dataset records rather than a live sensor feed.

The health score is rule-based, not a trained or validated machine-learning model. A recorded failure is marked Critical with a score of 0. Otherwise, the score starts at 100 and is reduced by:

- 25 points for tool wear of at least 200 minutes;
- 20 points for a temperature gap of at least 12 K;
- 15 points for torque of at least 60 Nm;
- 10 points for rotational speed of at least 2,000 rpm.

A score below 70 is shown as "Needs attention."

### Module 4: AI Maintenance Assistant

The assistant is designed to operate with a locally running Ollama server. Its default configuration is:

- URL: `http://localhost:11434`
- model: `llama3.2:latest`

Both can be changed through the `OLLAMA_URL` and `OLLAMA_MODEL` environment variables.

AI features include:

- quick maintenance assessment for a selected machine;
- conversational questions about the selected machine;
- streamed detailed maintenance reports;
- Markdown download of the latest report;
- schedule-based preventive-maintenance recommendations.

The code sends selected-record values such as temperatures, RPM, torque, tool wear, workload, recorded status, and recorded failure modes as context. Prompts instruct the model to use only the supplied record, avoid inventing telemetry or history, and recommend qualified maintenance review.

The streamed report is prompted to use exactly 155 words. If the generated output has fewer than 150 words, the code can append safe operational limitations. Because longer output is not truncated, exact length is not guaranteed.

The application remains usable for non-AI functionality when Ollama is unavailable.

### Modules 5 and 6: Work Order Management

Corrective work orders can be created only for machines whose dataset row has a recorded machine failure. New corrective orders are created with `Open` status and `High` priority.

Features include:

- persistent SQLite work-order storage;
- search by order ID, Product ID, failure reason, or recommended action;
- filters for status and priority;
- status and priority updates;
- work-order KPIs;
- CSV and JSON export;
- work-order deletion after confirmation;
- a database-level guard against more than one active order for the same Product ID.

Recorded failure codes map to rule-based action text. For example, power failures are mapped to inspection of the power train, electrical supply, and operating load.

### Module 7: Preventive Maintenance

The preventive-maintenance module supports:

- creation of recurring maintenance schedules;
- Daily, Weekly, Monthly, Quarterly, and Yearly frequencies;
- technician assignment;
- upcoming and overdue schedule views;
- schedule instructions;
- required or optional checklist items;
- generation of due preventive work orders;
- completion of work orders with technician and notes;
- maintenance-history tracking;
- AI recommendations grounded in a schedule, checklist, and recorded history.

When the Preventive Maintenance page is rendered, due active schedules can generate one preventive work order and advance to their next due date. The code prevents generation if an order for that same schedule/due date already exists or the machine already has a non-closed order. Required checklist items must be completed before maintenance completion can be recorded.

## 9. Database design and SQL work

There are no standalone `.sql` scripts. Database operations are implemented in Python using SQLite and parameterized SQL statements.

### Authentication database: `facility_auth.db`

The `users` table stores:

- auto-increment user ID;
- name;
- case-insensitive unique username;
- password hash;
- salt;
- creation timestamp.

Passwords use a per-user 16-byte random salt and PBKDF2-HMAC-SHA256 with 600,000 iterations. Hash comparison uses `hmac.compare_digest`.

### Maintenance database: `maintenance_work_orders.db`

The database includes:

- `work_orders`;
- `maintenance_schedules`;
- `maintenance_checklists`;
- `maintenance_checklist_results`;
- `maintenance_history`.

Important SQL/database implementation details:

- schema creation uses `CREATE TABLE IF NOT EXISTS`;
- newer work-order columns are added through checked `ALTER TABLE` statements;
- SQL parameters are passed separately from queries;
- a partial unique index named `one_active_order_per_machine` enforces at most one non-closed work order per machine;
- maintenance schedules are queried by due date and automatically advanced after order generation;
- required checklist completion is verified with a SQL join before a work order can be closed.

## 10. Machine learning and statistical methods

No trained machine-learning model is included in the repository. There is no classifier, regression model, clustering, forecasting, anomaly detector, training pipeline, test split, or evaluation metric such as accuracy, precision, recall, F1 score, or ROC-AUC.

The project uses:

- descriptive statistics;
- correlation analysis;
- grouped aggregates and failure-rate calculations;
- rule-based health assessments;
- local LLM-generated text grounded in selected historical records.

The health thresholds are authored application rules and are not shown as data-trained or statistically validated thresholds.

## 11. Quantifiable project information

| Item | Verified value |
|---|---:|
| Dataset rows | 10,000 |
| Source columns | 14 |
| Derived application fields | 3 |
| Missing source values | 0 |
| Recorded machine failures | 339 |
| Recorded failure rate | 3.39% |
| Machine types | 3 |
| Failure modes | 5 |
| Work-order priorities | 4 |
| Work-order statuses | 3 |
| Preventive-maintenance frequencies | 5 |
| Password-hash iterations | 600,000 |
| Target AI report length | 155 words |

No measured business savings, downtime reduction, model performance, response-time benchmark, production usage metric, or deployment metric is documented in the repository.

## 12. Important source files

| File | Responsibility |
|---|---|
| `app.py` | Main Streamlit interface, styling, data loading, filters, routing, dashboards, machine exploration, AI UI, work-order UI, and preventive-maintenance UI. |
| `work_orders.py` | SQLite schema setup and business logic for work orders, preventive schedules, checklists, due-order generation, and completion history. |
| `ai.py` | Ollama API requests, machine/schedule context construction, AI prompts, and streamed report support. |
| `auth.py` | User registration, authentication, password hashing, and user-table initialization. |
| `ai4i2020.csv` | Historical predictive-maintenance records consumed by the application. |
| `maintenance_work_orders.db` | Local persisted work-order and preventive-maintenance data. |
| `facility_auth.db` | Local persisted user-account data. |
| `requirements.txt` | Pinned Python dependencies. |
| `README.md` | Installation instructions and a high-level module summary. |

## 13. Skills demonstrated

- Python development
- Streamlit application development
- Exploratory data analysis
- Interactive dashboard development
- pandas data loading, transformation, aggregation, and export
- Plotly visualizations and gauge indicators
- SQLite relational schema design and CRUD operations
- Parameterized SQL usage
- Preventive and corrective maintenance workflow design
- Local LLM integration using Ollama
- Grounded prompt design for operational support
- Streaming AI output handling
- Local authentication and secure password hashing
- CSV, JSON, and Markdown export features
- Git-based iterative development

## 14. Limitations and recommended improvements

- Add automated tests for database logic, schedule date calculations, authentication validation, and UI workflows.
- Add linting, formatting, and continuous-integration configuration.
- Document dataset provenance, licensing, a data dictionary, and dataset limitations when authoritative source information is available.
- Validate or replace the heuristic health thresholds with a documented statistical or machine-learning approach if predictive performance is required.
- Add model evaluation and explainability if a predictive-maintenance model is introduced.
- Replace page-render-triggered preventive-order generation with a controlled background scheduler if independent automation is required.
- Consider a multi-user production database and role-based access control for larger deployments.
- Add audit logging, password reset/account management, session timeout, and deployment security controls for production use.
- Integrate real equipment telemetry, a CMMS, notifications, or calendar systems only if project scope and permissions require it.
- Add AI response evaluation, model/version logging, and stronger input/prompt-security controls.
- Review the work-order deletion UI and cover it with tests: it appears under the maintenance-history tab and uses an `order` variable produced in an earlier loop.
- Correct the `ai.py` module docstring reference to `module_3.py`; the repository's current UI is in `app.py`.

## 15. Conclusion

Agentic AI for Smart Facility Operations and Optimization Group 2 demonstrates an end-to-end local facility-operations prototype. It combines historical predictive-maintenance analysis, interactive machine exploration, local AI-assisted maintenance guidance, corrective work-order management, and recurring preventive-maintenance operations. The repository demonstrates how historical condition data can be connected to practical maintenance workflows while keeping the project clear about the limits of dataset-based, non-live decision support.
