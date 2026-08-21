# 🤖 AI-Powered Predictive Maintenance System

An AI-powered predictive maintenance and machine management system developed using Python and Streamlit. The system combines machine learning, data analysis, interactive dashboards, AI assistance, work-order management, preventive maintenance scheduling, maintenance tracking, and administrative authentication into a unified application.

---

## 📌 Project Overview

The **AI-Powered Predictive Maintenance System** is designed to support proactive machine maintenance by analyzing machine data and providing tools for monitoring, maintenance planning, work-order management, and preventive maintenance execution.

The application provides a centralized platform where users can analyze machine information, explore machine conditions, obtain AI-assisted maintenance recommendations, create and manage work orders, schedule preventive maintenance activities, track upcoming and overdue maintenance, maintain inspection checklists, and record completed maintenance activities.

The system is organized into seven major modules and provides an integrated workflow from machine data analysis to maintenance execution and history tracking.

---

## 🎯 Project Objectives

The main objectives of this project are:

- Analyze industrial machine and sensor data.
- Identify patterns related to machine failures.
- Provide machine-level information and insights.
- Support proactive and preventive maintenance planning.
- Create and manage maintenance schedules.
- Configure maintenance frequency.
- Assign technicians to maintenance activities.
- Track upcoming and overdue maintenance.
- Manage maintenance inspection checklists.
- Generate preventive maintenance work orders.
- Manage maintenance work orders.
- Record completed maintenance activities.
- Maintain maintenance history.
- Provide KPI-based maintenance monitoring.
- Generate AI-based maintenance recommendations.
- Provide downloadable AI-generated maintenance reports.
- Provide administrative authentication for application access.

---

# 🧩 System Modules

The application consists of seven major modules.

---

## 📊 Module 1 — Exploratory Data Analysis

This module focuses on understanding and analyzing the machine dataset.

The module provides functionality for:

- Dataset exploration
- Data inspection
- Statistical analysis
- Data distributions
- Machine-related analysis
- Failure-related analysis
- Exploratory visualizations

The purpose of this module is to understand the underlying machine data before applying predictive analytics and maintenance workflows.

---

## 📈 Module 2 — Dashboard

The Dashboard module provides an interactive overview of the machine and maintenance environment.

It provides:

- Machine information
- Maintenance-related information
- KPI-based summaries
- Interactive visualizations
- Machine status information
- Filtering capabilities

The dashboard helps users obtain a quick overview of the overall system.

---

## 🔍 Module 3 — Machine Explorer

The Machine Explorer allows users to inspect individual machine records.

It helps users analyze:

- Machine characteristics
- Machine-related parameters
- Operational information
- Machine condition
- Failure-related information
- Maintenance requirements

This module provides a more detailed machine-level view compared with the overall dashboard.

---

## 🤖 Module 4 — AI Assistant

The AI Assistant provides an AI-powered interface for maintenance-related assistance.

It can be used to:

- Ask maintenance-related questions
- Obtain AI-assisted maintenance guidance
- Analyze machine-related information
- Generate maintenance insights
- Support maintenance decision-making

The AI Assistant helps users interact with the system using natural-language queries.

---

## 🛠️ Module 5 — Work Order Creation Console

The Work Order Creation Console provides functionality for creating maintenance work orders.

Users can create work orders using information such as:

- Product ID
- Machine type
- Technician
- Priority
- Maintenance type
- Description
- Work-order status

This module provides the initial creation workflow for maintenance work orders.

---

## 🔧 Module 6 — Work Order Management

The Work Order Management module provides centralized management of maintenance work orders.

The module supports:

- Viewing work orders
- Searching work orders
- Filtering work orders
- Tracking work-order status
- Monitoring open work orders
- Monitoring work orders in progress
- Tracking completed work orders
- Managing maintenance activities

Preventive maintenance schedules from Module 7 can also be converted into work orders and managed through this module.

---

# 🛡️ Module 7 — Preventive Maintenance

The Preventive Maintenance module provides a complete preventive maintenance workflow.

It supports:

- Creating preventive maintenance schedules
- Configuring maintenance frequency
- Assigning technicians
- Tracking maintenance schedules
- Maintaining a maintenance calendar
- Tracking upcoming maintenance
- Monitoring overdue maintenance
- Managing maintenance checklists
- Completing maintenance activities
- Recording maintenance history
- Tracking maintenance status
- Generating preventive maintenance work orders
- Preventing duplicate active work orders
- Monitoring maintenance KPIs
- Generating AI-based maintenance recommendations
- Downloading AI-generated maintenance reports

---

## 📅 Preventive Maintenance Scheduling

Users can create preventive maintenance schedules by configuring:

- Product ID
- Machine type
- Maintenance type
- Maintenance frequency
- Start date
- Technician
- Description

The system calculates the next maintenance due date based on the selected maintenance frequency.

Supported maintenance frequencies include:

- Daily
- Weekly
- Monthly
- Quarterly
- Every 6 Months
- Yearly

---

## 📊 Preventive Maintenance Dashboard

The Preventive Maintenance dashboard provides KPI cards for monitoring the current maintenance situation.

The dashboard tracks:

- Total Schedules
- Scheduled Maintenance
- In-Progress Maintenance
- Completed Maintenance
- Overdue Maintenance

These KPIs provide a quick summary of the preventive maintenance workload.

---

## 📅 Maintenance Calendar

The Maintenance Calendar provides a calendar-based representation of preventive maintenance schedules.

Maintenance activities are visually categorized using status indicators:

- 🟢 Scheduled
- 🔴 Overdue
- 🔵 Completed

The calendar helps maintenance personnel understand when maintenance activities are scheduled.

---

## ⏰ Upcoming & Overdue Maintenance

The system provides an Upcoming & Overdue Maintenance section.

It displays information such as:

- PM ID
- Product ID
- Machine Type
- Maintenance Type
- Technician
- Next Due Date
- Days Remaining
- Priority
- Status

This allows maintenance personnel to identify upcoming maintenance activities and overdue maintenance activities.

---

## ✅ Maintenance Checklist

The Preventive Maintenance module provides an inspection checklist for maintenance activities.

The checklist includes:

- Inspect machine condition
- Check operating temperature
- Check rotational speed
- Check torque condition
- Inspect tool wear
- Verify overall machine condition

The system calculates checklist completion percentage.

Maintenance cannot be marked as completed until all required checklist items are completed.

---

## 📜 Maintenance History

Completed maintenance activities are stored in the Maintenance History section.

The history records information including:

- History ID
- PM ID
- Product ID
- Machine Type
- Maintenance Type
- Frequency
- Technician
- Scheduled Date
- Completed Date
- Status
- Checklist Progress
- Maintenance Notes

The system also provides maintenance history KPIs such as:

- Total Maintenance Records
- Completed Maintenance
- Average Checklist Completion

---

## 🔄 Preventive Maintenance Workflow

The preventive maintenance workflow is:

```text
Create Preventive Maintenance Schedule
                ↓
Configure Maintenance Frequency
                ↓
Assign Technician
                ↓
Monitor Maintenance Schedule
                ↓
Upcoming / Overdue Tracking
                ↓
Maintenance Checklist
                ↓
Complete Maintenance
                ↓
Record Maintenance History
                ↓
Calculate Next Maintenance Date
                ↓
Generate Preventive Maintenance Work Order
                ↓
Manage Work Order
```
