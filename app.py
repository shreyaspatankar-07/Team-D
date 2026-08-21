import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ollama
import os
import sqlite3
import calendar

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Machine Predictive Maintenance Dashboard",
    page_icon="⚙️",
    layout="wide"
)

# ==================================================
# ADMIN LOGIN AUTHENTICATION
# ==================================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def admin_login():

    st.title("🔐 Admin Login")

    st.caption(
        "Machine Predictive Maintenance System"
    )

    st.divider()

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        st.subheader(
            "Administrator Authentication"
        )

        username = st.text_input(
            "👤 Username",
            placeholder="Enter admin username",
            key="login_username"
        )

        password = st.text_input(
            "🔑 Password",
            type="password",
            placeholder="Enter admin password",
            key="login_password"
        )

        login_button = st.button(
            "🔓 Login",
            use_container_width=True,
            type="primary"
        )

        if login_button:

            if (
                username == ADMIN_USERNAME
                and password == ADMIN_PASSWORD
            ):

                st.session_state[
                    "authenticated"
                ] = True

                st.success(
                    "✅ Login successful!"
                )

                st.rerun()

            else:

                st.session_state[
                    "authenticated"
                ] = False

                st.error(
                    "❌ Invalid username or password."
                )


# ==================================================
# CHECK AUTHENTICATION
# ==================================================

if "authenticated" not in st.session_state:

    st.session_state[
        "authenticated"
    ] = False


if not st.session_state[
    "authenticated"
]:

    admin_login()

    st.stop()

# ==================================================
# LOAD DATASET
# ==================================================

@st.cache_data
def load_data():
    return pd.read_csv("ai4i2020.csv")

df = load_data()


# ==================================================
# PROFESSIONAL PDF REPORT GENERATOR
# ==================================================

def generate_pdf(report_text, machine):

    # Create reports folder if it doesn't exist
    os.makedirs("reports", exist_ok=True)

    file_name = os.path.join(
        "reports",
        f"Maintenance_Report_{machine['Product ID']}.pdf"
    )

    doc = SimpleDocTemplate(file_name)

    styles = getSampleStyleSheet()

    story = []

    # --------------------------------------------------
    # Title
    # --------------------------------------------------

    story.append(
        Paragraph(
            "<font size=22><b>AI Predictive Maintenance Report</b></font>",
            styles["Title"]
        )
    )

    story.append(
        Paragraph("<br/>", styles["Normal"])
    )

    # --------------------------------------------------
    # Report Information
    # --------------------------------------------------

    story.append(
        Paragraph(
            f"<b>Generated On :</b> {datetime.now().strftime('%d-%B-%Y %I:%M %p')}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Product ID :</b> {machine['Product ID']}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Machine Type :</b> {machine['Type']}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph("<br/>", styles["Normal"])
    )

    # --------------------------------------------------
    # Sensor Readings
    # --------------------------------------------------

    story.append(
        Paragraph(
            "<b><font size=16>Machine Sensor Readings</font></b>",
            styles["Heading2"]
        )
    )

    sensor_data = [

        f"Air Temperature : {machine['Air temperature [K]']:.1f} K",

        f"Process Temperature : {machine['Process temperature [K]']:.1f} K",

        f"Rotational Speed : {machine['Rotational speed [rpm]']:.0f} RPM",

        f"Torque : {machine['Torque [Nm]']:.1f} Nm",

        f"Tool Wear : {machine['Tool wear [min]']:.0f} minutes"

    ]

    for item in sensor_data:

        story.append(
            Paragraph(item, styles["BodyText"])
        )

    story.append(
        Paragraph("<br/>", styles["Normal"])
    )

    # --------------------------------------------------
    # AI Report
    # --------------------------------------------------

    story.append(
        Paragraph(
            "<b><font size=16>AI Maintenance Analysis</font></b>",
            styles["Heading2"]
        )
    )

    for line in report_text.split("\n"):

        if line.strip() != "":

            story.append(
                Paragraph(line, styles["BodyText"])
            )

    story.append(
        Paragraph("<br/>", styles["Normal"])
    )

    story.append(
        Paragraph(
            "<b>End of AI Maintenance Report</b>",
            styles["Heading2"]
        )
    )

    doc.build(story)

    return file_name


def generate_work_order_pdf(order):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "WorkOrderTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "WorkOrderSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=10,
        leading=14
    )

    story = []

    # ==================================================
    # TITLE
    # ==================================================

    story.append(
        Paragraph(
            "MACHINE PREDICTIVE MAINTENANCE",
            title_style
        )
    )

    story.append(
        Paragraph(
            "MAINTENANCE WORK ORDER",
            subtitle_style
        )
    )

    # ==================================================
    # WORK ORDER HEADER
    # ==================================================

    story.append(
        Paragraph(
            f"<b>Work Order ID:</b> {order['WO_ID']}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Created Date:</b> {order['created_date']}",
            normal_style
        )
    )

    story.append(Spacer(1, 15))

    # ==================================================
    # WORK ORDER DETAILS
    # ==================================================

    story.append(
        Paragraph(
            "Work Order Details",
            heading_style
        )
    )

    details = [
        ["Field", "Details"],
        ["Work Order ID", str(order["WO_ID"])],
        ["Product ID", str(order["product_id"])],
        ["Machine Type", str(order["machine_type"])],
        ["Technician", str(order["technician"])],
        ["Priority", str(order["priority"])],
        ["Maintenance Type", str(order["maintenance_type"])],
        ["Status", str(order["status"])],
        ["Created Date", str(order["created_date"])]
    ]

    details_table = Table(
        details,
        colWidths=[150, 330]
    )

    details_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F2937")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (0, -1),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(details_table)

    story.append(Spacer(1, 20))

    # ==================================================
    # MAINTENANCE DESCRIPTION
    # ==================================================

    story.append(
        Paragraph(
            "Maintenance Description",
            heading_style
        )
    )

    description = str(order["description"])

    story.append(
        Paragraph(
            description.replace("\n", "<br/>"),
            normal_style
        )
    )

    story.append(Spacer(1, 30))

    # ==================================================
    # FOOTER / NOTE
    # ==================================================

    story.append(
        Paragraph(
            "Generated by Machine Predictive Maintenance Platform",
            subtitle_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()

def initialize_preventive_maintenance_db():

    conn = sqlite3.connect("maintenance.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preventive_maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pm_id TEXT UNIQUE,
            product_id TEXT NOT NULL,
            machine_type TEXT,
            maintenance_type TEXT NOT NULL,
            frequency TEXT NOT NULL,
            start_date TEXT NOT NULL,
            next_due_date TEXT,
            technician TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            description TEXT,
            created_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pm_id TEXT NOT NULL,
            inspect_machine INTEGER DEFAULT 0,
            check_temperature INTEGER DEFAULT 0,
            check_rotational_speed INTEGER DEFAULT 0,
            check_torque INTEGER DEFAULT 0,
            inspect_tool_wear INTEGER DEFAULT 0,
            verify_machine_condition INTEGER DEFAULT 0,
            completion_percentage REAL DEFAULT 0,
            updated_date TEXT
        )
    """)

    conn.commit()
    conn.close()

initialize_preventive_maintenance_db()

# ==================================================
# CALCULATE NEXT PREVENTIVE MAINTENANCE DATE
# ==================================================
def calculate_next_maintenance_date(
    current_date,
    frequency
):

    if frequency == "Daily":

        return current_date + timedelta(days=1)

    elif frequency == "Weekly":

        return current_date + relativedelta(
            weeks=1
        )

    elif frequency == "Monthly":

        return current_date + relativedelta(
            months=1
        )

    elif frequency == "Quarterly":

        return current_date + relativedelta(
            months=3
        )

    elif frequency == "Every 6 Months":

        return current_date + relativedelta(
            months=6
        )

    elif frequency == "Yearly":

        return current_date + relativedelta(
            years=1
        )

    else:

        return current_date

# ==================================================
# GENERATE NEXT PREVENTIVE MAINTENANCE ID
# ==================================================

def generate_next_pm_id(cursor):

    cursor.execute(
        """
        SELECT pm_id
        FROM preventive_maintenance
        WHERE pm_id LIKE 'PM-%'
        ORDER BY id DESC
        LIMIT 1
        """
    )

    result = cursor.fetchone()

    if result is None:
        return "PM-0001"

    last_pm_id = result[0]

    try:
        last_number = int(
            last_pm_id.replace("PM-", "")
        )

        next_number = last_number + 1

        return f"PM-{next_number:04d}"

    except (ValueError, TypeError):

        return "PM-0001"

# ==================================================
# SQLITE DATABASE
# ==================================================

def initialize_database():

    conn = sqlite3.connect("maintenance.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS work_orders(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        product_id TEXT,

        machine_type TEXT,

        technician TEXT,

        priority TEXT,

        maintenance_type TEXT,

        description TEXT,

        status TEXT,

        created_date TEXT

    )
    """)

    conn.commit()

    conn.close()

initialize_database()

# ==================================================
# SIDEBAR
# ==================================================


st.sidebar.title("⚙️ Machine Predictive Maintenance")

st.sidebar.markdown("---")

page = st.sidebar.radio(

    "Module Navigation",

    [

        "Module 1 : EDA",

        "Module 2 : Dashboard",

        "Module 3 : Machine Explorer",

        "Module 4 : AI Assistant",

        "Module 5 : Work Order Creation Console",

        "Module 6 : Work Order Management",

        "Module 7 : Preventive Maintenance"

    ]

)

st.sidebar.markdown("---")

st.sidebar.subheader("🔍 Dashboard Filters")

st.sidebar.write("Filter machine operational records")

machine_types = sorted(df["Type"].unique())

selected_types = st.sidebar.multiselect(

    "Machine Type",

    machine_types,

    default=machine_types

)

failure_status = st.sidebar.selectbox(

    "Machine Status",

    [

        "All Machines",

        "Healthy Machines",

        "Failed Machines"

    ]

)

# ==================================================
# FILTER DATA
# ==================================================

filtered_df = df[
    df["Type"].isin(selected_types)
].copy()

if failure_status == "Healthy Machines":

    filtered_df = filtered_df[
        filtered_df["Machine failure"] == 0
    ]

elif failure_status == "Failed Machines":

    filtered_df = filtered_df[
        filtered_df["Machine failure"] == 1
    ]

if filtered_df.empty:

    st.warning(
        "No machine records match the selected filters."
    )

    st.stop()

# ==================================================
# MODULE 1
# ==================================================

if page == "Module 1 : EDA":

    st.title("📊 Module 1 : Exploratory Data Analysis")

    st.info(
        """
        This page summarizes the exploratory data analysis
        performed during Module 1.

        ✔ Dataset Overview

        ✔ Data Cleaning

        ✔ Missing Value Analysis

        ✔ Descriptive Statistics

        ✔ Distribution Analysis

        ✔ Correlation Analysis

        ✔ Heatmaps

        ✔ Histograms

        ✔ Boxplots

        ✔ Scatter Plots
        """
    )

    st.subheader("Dataset Preview")

    st.dataframe(
        df.head(20),
        use_container_width=True
    )

    st.divider()

    st.subheader("Dataset Information")

    info1, info2, info3 = st.columns(3)

    info1.metric("Rows", len(df))
    info2.metric("Columns", df.shape[1])
    info3.metric("Missing Values", df.isnull().sum().sum())


    st.divider()

    st.subheader("Machine Type Distribution")

    type_fig = px.pie(
        df,
        names="Type",
        title="Distribution of Machine Types",
        hole=0.45
    )

    st.plotly_chart(
        type_fig,
        use_container_width=True
    )

    st.divider()

    st.subheader("Machine Failure Distribution")

    failure_counts = (
        df["Machine failure"]
        .map({0: "Healthy", 1: "Failed"})
        .value_counts()
        .reset_index()
    )

    failure_counts.columns = ["Status", "Count"]

    failure_fig = px.bar(
        failure_counts,
        x="Status",
        y="Count",
        color="Status",
        text="Count",
        title="Healthy vs Failed Machines"
    )

    failure_fig.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        failure_fig,
        use_container_width=True
    )

    st.divider()

    st.subheader("Correlation Heatmap")

    corr = df.select_dtypes(
        include=["int64", "float64"]
    ).corr()

    heatmap = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        aspect="auto"
    )

    st.plotly_chart(
        heatmap,
        use_container_width=True
    )

    st.divider()

    st.subheader("Tool Wear Distribution")

    hist = px.histogram(
        df,
        x="Tool wear [min]",
        nbins=40,
        title="Distribution of Tool Wear"
    )

    st.plotly_chart(
        hist,
        use_container_width=True
    )

    st.divider()

    st.subheader("Air Temperature vs Process Temperature")

    scatter = px.scatter(
        df,
        x="Air temperature [K]",
        y="Process temperature [K]",
        color="Type",
        opacity=0.6
    )

    st.plotly_chart(
        scatter,
        use_container_width=True
    )

# ==================================================
# MODULE 2
# ==================================================

elif page == "Module 2 : Dashboard":

    st.title("📊 Machine Predictive Maintenance Dashboard")

    st.caption(
        "Operational Analytics, Failure Monitoring & Exploratory Data Insights"
    )

    # ==================================================
    # KPI CALCULATIONS
    # ==================================================

    total_records = len(filtered_df)

    healthy_machines = (
        filtered_df["Machine failure"] == 0
    ).sum()

    failed_machines = (
        filtered_df["Machine failure"] == 1
    ).sum()

    failure_rate = (
        failed_machines / total_records
    ) * 100

    average_rpm = filtered_df[
        "Rotational speed [rpm]"
    ].mean()

    average_tool_wear = filtered_df[
        "Tool wear [min]"
    ].mean()

    average_torque = filtered_df[
        "Torque [Nm]"
    ].mean()

    # ==================================================
    # KPI CARDS
    # ==================================================

    st.subheader("📊 Machine Health Overview")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric(
        "📊 Total Records",
        f"{total_records:,}"
    )

    kpi2.metric(
        "✅ Healthy Machines",
        f"{healthy_machines:,}"
    )

    kpi3.metric(
        "❌ Failed Machines",
        f"{failed_machines:,}"
    )

    kpi4.metric(
        "⚠️ Failure Rate",
        f"{failure_rate:.2f}%"
    )

    kpi5, kpi6, kpi7 = st.columns(3)

    kpi5.metric(
        "⚙️ Average RPM",
        f"{average_rpm:.2f}"
    )

    kpi6.metric(
        "🔧 Average Tool Wear",
        f"{average_tool_wear:.2f} min"
    )

    kpi7.metric(
        "🔩 Average Torque",
        f"{average_torque:.2f} Nm"
    )

    st.divider()

    # ==================================================
    # MACHINE FAILURE AND MACHINE TYPE DISTRIBUTION
    # ==================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("❌ Machine Failure Distribution")

        failure_data = (
            filtered_df["Machine failure"]
            .value_counts()
            .reindex([0, 1], fill_value=0)
            .reset_index()
        )

        failure_data.columns = [
            "Machine Failure",
            "Count"
        ]

        failure_data["Status"] = failure_data[
            "Machine Failure"
        ].map({
            0: "Healthy",
            1: "Failed"
        })

        failure_fig = px.bar(
            failure_data,
            x="Status",
            y="Count",
            color="Status",
            text="Count",
            title="Healthy vs Failed Machine Records"
        )

        failure_fig.update_traces(
            textposition="outside"
        )

        failure_fig.update_layout(
            showlegend=False
        )

        st.plotly_chart(
            failure_fig,
            use_container_width=True
        )

    with col2:

        st.subheader("🏭 Machine Type Distribution")

        type_data = (
            filtered_df["Type"]
            .value_counts()
            .reset_index()
        )

        type_data.columns = [
            "Machine Type",
            "Count"
        ]

        type_fig = px.pie(
            type_data,
            names="Machine Type",
            values="Count",
            hole=0.45,
            title="Distribution of Machine Types"
        )

        type_fig.update_traces(
            textinfo="percent+label"
        )

        st.plotly_chart(
            type_fig,
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # IMPORTANT EDA FAILURE INSIGHTS
    # ==================================================

    st.subheader("📈 Machine Failure EDA Insights")

    failure_analysis_df = filtered_df.copy()

    failure_analysis_df["Machine Status"] = (
        failure_analysis_df["Machine failure"]
        .map({
            0: "Healthy",
            1: "Failed"
        })
    )

    eda_col1, eda_col2 = st.columns(2)

    with eda_col1:

        type_failure = (
            filtered_df
            .groupby("Type")["Machine failure"]
            .agg(["count", "sum"])
            .reset_index()
        )

        type_failure["Failure Rate (%)"] = (
            type_failure["sum"]
            / type_failure["count"]
        ) * 100

        failure_rate_fig = px.bar(
            type_failure,
            x="Type",
            y="Failure Rate (%)",
            color="Type",
            text="Failure Rate (%)",
            title="Machine Failure Rate by Machine Type"
        )

        failure_rate_fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        failure_rate_fig.update_layout(
            showlegend=False,
            xaxis_title="Machine Type",
            yaxis_title="Failure Rate (%)"
        )

        st.plotly_chart(
            failure_rate_fig,
            use_container_width=True
        )

    with eda_col2:

        torque_failure_fig = px.box(
            failure_analysis_df,
            x="Machine Status",
            y="Torque [Nm]",
            color="Machine Status",
            points="outliers",
            title="Torque Distribution by Machine Status"
        )

        st.plotly_chart(
            torque_failure_fig,
            use_container_width=True
        )

    eda_col3, eda_col4 = st.columns(2)

    with eda_col3:

        tool_wear_failure_fig = px.box(
            failure_analysis_df,
            x="Machine Status",
            y="Tool wear [min]",
            color="Machine Status",
            points="outliers",
            title="Tool Wear Distribution by Machine Status"
        )

        st.plotly_chart(
            tool_wear_failure_fig,
            use_container_width=True
        )

    with eda_col4:

        # NEW EDA PLOT
        # Tool Wear vs Torque by Machine Status

        tool_wear_torque_fig = px.scatter(
            failure_analysis_df,
            x="Tool wear [min]",
            y="Torque [Nm]",
            color="Machine Status",
            title="Tool Wear vs Torque by Machine Status",
            opacity=0.65,
            hover_data=[
                "Product ID",
                "Type",
                "Rotational speed [rpm]"
            ]
        )

        tool_wear_torque_fig.update_layout(
            xaxis_title="Tool Wear [min]",
            yaxis_title="Torque [Nm]"
        )

        st.plotly_chart(
            tool_wear_torque_fig,
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # HEATMAP 1
    # FIXED CORRELATION FROM COMPLETE DATASET
    # ==================================================

    st.subheader("🔥 Correlation Matrix of Numerical Attributes")

    numerical_cols = [
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]"
    ]

    # IMPORTANT:
    # Uses complete dataset exactly like Module 1
    correlation_matrix = df[
        numerical_cols
    ].corr()

    heatmap_1 = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale="RdBu",
            reversescale=True,
            text=correlation_matrix.round(2).values,
            texttemplate="%{text:.2f}",
            textfont=dict(size=13),
            colorbar=dict(
                title="Correlation"
            ),
            hovertemplate=(
                "%{x}<br>"
                "%{y}<br>"
                "Correlation: %{z:.3f}"
                "<extra></extra>"
            )
        )
    )

    heatmap_1.update_layout(
        title="Correlation Matrix of Numerical Attributes",
        height=650,
        xaxis=dict(
            side="bottom",
            tickangle=-25,
            automargin=True
        ),
        yaxis=dict(
            autorange="reversed",
            automargin=True
        ),
        margin=dict(
            l=180,
            r=80,
            t=80,
            b=150
        )
    )

    st.plotly_chart(
        heatmap_1,
        use_container_width=True
    )

    st.info(
        """
        This heatmap uses the complete machine predictive maintenance
        dataset and the same five numerical attributes selected in
        Module 1. The heatmap remains constant when dashboard filters
        are changed.

        Air temperature and process temperature show a strong positive
        relationship, while rotational speed and torque show a strong
        negative relationship.
        """
    )

    st.divider()

    # ==================================================
    # HEATMAP 2
    # COMPLETE DATASET CORRELATION
    # ==================================================

    st.subheader("🔥 Complete Correlation Heatmap")

    # IMPORTANT:
    # Uses complete original dataset instead of filtered data
    all_numerical_df = df.select_dtypes(
        include=["int64", "float64"]
    )

    complete_correlation_matrix = (
        all_numerical_df.corr()
    )

    heatmap_2 = go.Figure(
        data=go.Heatmap(
            z=complete_correlation_matrix.values,
            x=complete_correlation_matrix.columns,
            y=complete_correlation_matrix.index,
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale="RdBu",
            reversescale=True,
            text=complete_correlation_matrix.round(2).values,
            texttemplate="%{text:.2f}",
            textfont=dict(size=10),
            colorbar=dict(
                title="Correlation"
            ),
            hovertemplate=(
                "%{x}<br>"
                "%{y}<br>"
                "Correlation: %{z:.3f}"
                "<extra></extra>"
            )
        )
    )

    heatmap_2.update_layout(
        title="Complete Correlation Heatmap",
        height=850,
        xaxis=dict(
            side="bottom",
            tickangle=-45,
            automargin=True
        ),
        yaxis=dict(
            autorange="reversed",
            automargin=True
        ),
        margin=dict(
            l=180,
            r=80,
            t=80,
            b=200
        )
    )

    st.plotly_chart(
        heatmap_2,
        use_container_width=True
    )

    st.info(
        """
        The complete correlation heatmap uses the complete original
        dataset and includes all integer and floating-point attributes.

        The correlation values remain constant when sidebar filters
        are changed. This provides additional insight into relationships
        between operational parameters, machine failure and individual
        failure modes.
        """
    )

    st.divider()

    # ==================================================
    # ATTRIBUTE RELATIONSHIP ANALYSIS
    # ==================================================

    st.subheader("🔗 Attribute Relationship Analysis")

    relationship_col1, relationship_col2 = st.columns(2)

    with relationship_col1:

        temp_scatter = px.scatter(
            filtered_df,
            x="Air temperature [K]",
            y="Process temperature [K]",
            color="Type",
            title="Air Temperature vs Process Temperature",
            opacity=0.6,
            hover_data=[
                "Product ID",
                "Machine failure"
            ]
        )

        st.plotly_chart(
            temp_scatter,
            use_container_width=True
        )

    with relationship_col2:

        rpm_torque_df = filtered_df.copy()

        rpm_torque_df["Machine Status"] = (
            rpm_torque_df["Machine failure"]
            .map({
                0: "Healthy",
                1: "Failed"
            })
        )

        rpm_torque_fig = px.scatter(
            rpm_torque_df,
            x="Rotational speed [rpm]",
            y="Torque [Nm]",
            color="Machine Status",
            title="Rotational Speed vs Torque",
            opacity=0.6,
            hover_data=[
                "Product ID",
                "Type",
                "Tool wear [min]"
            ]
        )

        st.plotly_chart(
            rpm_torque_fig,
            use_container_width=True
        )

    st.divider()

    # ==================================================
    # OPERATIONAL FEATURES VS MACHINE FAILURE
    # ==================================================

    st.subheader("⚠️ Operational Features vs Machine Failure")

    feature_options = [
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]"
    ]

    selected_feature = st.selectbox(
        "Select an operational feature for failure analysis",
        feature_options
    )

    feature_failure_df = filtered_df.copy()

    feature_failure_df["Machine Status"] = (
        feature_failure_df["Machine failure"]
        .map({
            0: "Healthy",
            1: "Failed"
        })
    )

    feature_failure_fig = px.box(
        feature_failure_df,
        x="Machine Status",
        y=selected_feature,
        color="Machine Status",
        title=f"{selected_feature} vs Machine Failure",
        points="outliers"
    )

    st.plotly_chart(
        feature_failure_fig,
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # RPM VS TOOL WEAR
    # ==================================================

    st.subheader("⚙️ RPM and Tool Wear Analysis")

    scatter_df = filtered_df.copy()

    scatter_df["Machine Status"] = (
        scatter_df["Machine failure"]
        .map({
            0: "Healthy",
            1: "Failed"
        })
    )

    scatter_fig = px.scatter(
        scatter_df,
        x="Rotational speed [rpm]",
        y="Tool wear [min]",
        color="Machine Status",
        hover_data=[
            "Product ID",
            "Type",
            "Torque [Nm]",
            "Air temperature [K]",
            "Process temperature [K]"
        ],
        title="Rotational Speed vs Tool Wear by Machine Status",
        opacity=0.65
    )

    st.plotly_chart(
        scatter_fig,
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # FAILURE MODE ANALYSIS
    # ==================================================

    st.subheader("🛠️ Failure Mode Analysis")

    failure_columns = [
        "TWF",
        "HDF",
        "PWF",
        "OSF",
        "RNF"
    ]

    failure_mode_counts = (
        filtered_df[failure_columns]
        .sum()
        .reset_index()
    )

    failure_mode_counts.columns = [
        "Failure Mode",
        "Count"
    ]

    failure_mode_names = {
        "TWF": "Tool Wear Failure",
        "HDF": "Heat Dissipation Failure",
        "PWF": "Power Failure",
        "OSF": "Overstrain Failure",
        "RNF": "Random Failure"
    }

    failure_mode_counts["Failure Mode"] = (
        failure_mode_counts["Failure Mode"]
        .map(failure_mode_names)
    )

    failure_mode_fig = px.bar(
        failure_mode_counts,
        x="Failure Mode",
        y="Count",
        color="Failure Mode",
        text="Count",
        title="Distribution of Machine Failure Modes"
    )

    failure_mode_fig.update_traces(
        textposition="outside"
    )

    failure_mode_fig.update_layout(
        showlegend=False,
        xaxis_title="Failure Mode",
        yaxis_title="Failure Count"
    )

    st.plotly_chart(
        failure_mode_fig,
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # DATASET EXPLORER
    # ==================================================

    st.subheader("📁 Machine Predictive Maintenance Dataset")

    dataset_col1, dataset_col2, dataset_col3 = st.columns(3)

    dataset_col1.metric(
        "Dataset Rows",
        f"{len(filtered_df):,}"
    )

    dataset_col2.metric(
        "Dataset Columns",
        f"{filtered_df.shape[1]}"
    )

    dataset_col3.metric(
        "Missing Values",
        f"{filtered_df.isnull().sum().sum():,}"
    )

    st.caption(
        "The dataset displayed below dynamically updates according "
        "to the Machine Type and Machine Status sidebar filters."
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=500
    )

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download Filtered Dataset",
        data=csv_data,
        file_name="filtered_machine_maintenance_dataset.csv",
        mime="text/csv"
    )

    st.divider()

    # ==================================================
    # DASHBOARD SUMMARY
    # ==================================================

    st.subheader("📋 Dashboard Summary")

    air_process_corr = correlation_matrix.loc[
        "Air temperature [K]",
        "Process temperature [K]"
    ]

    rpm_torque_corr = correlation_matrix.loc[
        "Rotational speed [rpm]",
        "Torque [Nm]"
    ]

    st.info(
        f"""
        The current dashboard view contains {total_records:,} machine records.
        Among these records, {healthy_machines:,} are healthy and
        {failed_machines:,} represent machine failures.

        The current machine failure rate is {failure_rate:.2f}%.

        Average rotational speed is {average_rpm:.2f} RPM,
        average tool wear is {average_tool_wear:.2f} minutes,
        and average torque is {average_torque:.2f} Nm.

        Based on the complete dataset, air temperature and process
        temperature show a correlation of {air_process_corr:.2f}.

        Based on the complete dataset, rotational speed and torque
        show a correlation of {rpm_torque_corr:.2f}.

        The dashboard combines exploratory data analysis with interactive
        machine failure monitoring to identify operational patterns,
        attribute relationships and failure behaviour.
        """
    )

# ==================================================
# MODULE 3
# ==================================================

elif page == "Module 3 : Machine Explorer":

    st.title("⚙️ Module 3 : Machine Explorer")

    st.caption(
        "Search and analyze an individual machine using Product ID."
    )

    st.subheader("Search by Product ID")

    product_id = st.text_input(
        "Enter Product ID",
        placeholder="Example : M14860"
    )

    # ==================================================
    # SEARCH PRODUCT ID
    # ==================================================

    if product_id.strip():
        search_result = df[
            df["Product ID"].astype(str).str.upper()
            == product_id.upper().strip()
        ]

        if search_result.empty:

            st.error("❌ Product ID not found.")

        else:

            st.success("✅ Product ID Found")

            machine = search_result.iloc[0]

            # ==================================================
            # MACHINE INFORMATION
            # ==================================================

            st.divider()

            st.subheader("Machine Information")

            info_col1, info_col2 = st.columns(2)

            with info_col1:

                st.metric(
                    "Product ID",
                    machine["Product ID"]
                )

                st.metric(
                    "Machine Type",
                    machine["Type"]
                )

                st.metric(
                    "UDI",
                    machine["UDI"]
                )

                st.metric(
                    "Air Temperature",
                    f'{machine["Air temperature [K]"]:.1f} K'
                )

            with info_col2:

                st.metric(
                    "Process Temperature",
                    f'{machine["Process temperature [K]"]:.1f} K'
                )

                st.metric(
                    "Rotational Speed",
                    f'{machine["Rotational speed [rpm]"]:.0f} RPM'
                )

                st.metric(
                    "Torque",
                    f'{machine["Torque [Nm]"]:.1f} Nm'
                )

                st.metric(
                    "Tool Wear",
                    f'{machine["Tool wear [min]"]:.0f} min'
                )

            # ==================================================
            # LIVE SENSOR VALUES
            # ==================================================

            st.divider()

            st.subheader("Live Sensor Values")

            sensor_col1, sensor_col2, sensor_col3, sensor_col4, sensor_col5 = st.columns(5)

            # ==================================================
            # AIR TEMPERATURE
            # ==================================================

            with sensor_col1:

                air_temp_fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=machine["Air temperature [K]"],

                        number={
                            "suffix": " K",
                            "font": {"size": 26}
                        },
                        title={
                            "text": "<b>Air Temp</b>",
                            "font": {"size": 22}
                        },
                        gauge={
                            "axis": {"range": [290, 310]},
                            "bar": {"color": "green"},
                            "steps": [
                                {"range": [290, 296], "color": "#ffcccc"},
                                {"range": [296, 302], "color": "#ccffcc"},
                                {"range": [302, 310], "color": "#ffe5b4"}
                            ]
                        }
                    )
                )

                air_temp_fig.update_layout(
                    height=225,
                    margin=dict(l=10, r=10, t=40, b=10)
                )

                st.plotly_chart(
                    air_temp_fig,
                    use_container_width=False
                )

            # ==================================================
            # PROCESS TEMPERATURE
            # ==================================================

            with sensor_col2:

                process_temp_fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=machine["Process temperature [K]"],

                        number={
                            "suffix": " K",
                            "font": {"size": 26}
                        },
                        title={
                            "text": "<b>Process Temp</b>",
                            "font": {"size": 22}
                        },
                        gauge={
                            "axis": {"range": [300, 320]},
                            "bar": {"color": "blue"},
                            "steps": [
                                {"range": [300, 306], "color": "#ffcccc"},
                                {"range": [306, 314], "color": "#ccffcc"},
                                {"range": [314, 320], "color": "#ffe5b4"}
                            ]
                        }
                    )
                )

                process_temp_fig.update_layout(
                    height=225,
                    margin=dict(l=10, r=10, t=40, b=10)
                )

                st.plotly_chart(
                    process_temp_fig,
                    use_container_width=False
                )

            # ==================================================
            # ROTATIONAL SPEED
            # ==================================================

            with sensor_col3:

                rpm_fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=machine["Rotational speed [rpm]"],

                        number={
                            "suffix": " RPM",
                            "font": {"size": 26}
                        },
                        title={
                            "text": "<b>RPM</b>",
                            "font": {"size": 22}
                        },
                        gauge={
                            "axis": {"range": [1000, 3000]},
                            "bar": {"color": "orange"},
                            "steps": [
                                {"range": [1000, 1500], "color": "#ffcccc"},
                                {"range": [1500, 2500], "color": "#ccffcc"},
                                {"range": [2500, 3000], "color": "#ffe5b4"}
                            ]
                        }
                    )
                )

                rpm_fig.update_layout(
                    height=225,
                    margin=dict(l=10, r=10, t=40, b=10)
                )

                st.plotly_chart(
                    rpm_fig,
                    use_container_width=False
                )

            # ==================================================
            # TORQUE
            # ==================================================

            with sensor_col4:

                torque_fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=machine["Torque [Nm]"],

                        number={
                            "suffix": " Nm",
                            "font": {"size": 26}
                        },
                        title={
                            "text": "<b>Torque</b>",
                            "font": {"size": 22}
                        },
                        gauge={
                            "axis": {"range": [0, 80]},
                            "bar": {"color": "purple"},
                            "steps": [
                                {"range": [0, 20], "color": "#ffcccc"},
                                {"range": [20, 50], "color": "#ccffcc"},
                                {"range": [50, 80], "color": "#ffe5b4"}
                            ]
                        }
                    )
                )

                torque_fig.update_layout(
                    height=225,
                    margin=dict(l=10, r=10, t=40, b=10)
                )

                st.plotly_chart(
                    torque_fig,
                    use_container_width=False
                )

            # ==================================================
            # TOOL WEAR
            # ==================================================

            with sensor_col5:

                tool_wear_fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=machine["Tool wear [min]"],

                        number={
                            "suffix": " min",
                            "font": {"size": 26}
                        },
                        title={
                            "text": "<b>Tool Wear</b>",
                            "font": {"size": 22}
                        },
                        gauge={
                            "axis": {"range": [0, 250]},
                            "bar": {"color": "red"},
                            "steps": [
                                {"range": [0, 80], "color": "#ccffcc"},
                                {"range": [80, 160], "color": "#ffe5b4"},
                                {"range": [160, 250], "color": "#ffcccc"}
                            ]
                        }
                    )
                )

                tool_wear_fig.update_layout(
                    height=225,
                    margin=dict(l=10, r=10, t=40, b=10)
                )

                st.plotly_chart(
                    tool_wear_fig,
                    use_container_width=False
                )

            # ==================================================
            # FAILURE ANALYSIS
            # ==================================================

            st.divider()

            st.subheader("Failure Analysis")

            # -------------------------
            # First Row
            # -------------------------

            failure_cols = st.columns(3)

            # Tool Wear Failure
            with failure_cols[0]:

                if machine["TWF"] == 1:
                    st.error("🔴 Tool Wear Failure")
                else:
                    st.success("🟢 Tool Wear : Normal")

            # Heat Dissipation Failure
            with failure_cols[1]:

                if machine["HDF"] == 1:
                    st.error("🔴 Heat Dissipation Failure")
                else:
                    st.success("🟢 Heat Dissipation : Normal")

            # Power Failure
            with failure_cols[2]:

                if machine["PWF"] == 1:
                    st.error("🔴 Power Failure")
                else:
                    st.success("🟢 Power Failure : Normal")


            # -------------------------
            # Second Row
            # -------------------------

            failure_cols2 = st.columns(2)

            # Overstrain Failure
            with failure_cols2[0]:

                if machine["OSF"] == 1:
                    st.error("🔴 Overstrain Failure")
                else:
                    st.success("🟢 Overstrain : Normal")

            # Random Failure
            with failure_cols2[1]:

                if machine["RNF"] == 1:
                    st.error("🔴 Random Failure")
                else:
                    st.success("🟢 Random Failure : Normal")

            # ==================================================
            # HEALTH STATUS
            # ==================================================

            st.divider()

            st.subheader("Health Status")

            failure_detected = (
                machine["Machine failure"] == 1
            )

            if failure_detected:

                st.error(
                    """
            🔴 **Machine Failure Detected**

            This machine has experienced a failure.

            Immediate inspection and maintenance are recommended.
            """
                )

            else:

                st.success(
                    """
            🟢 **Healthy Machine**

            This machine is operating under normal conditions.

            No machine failure has been detected.
            """
                )

# ==================================================
# MODULE 4
# ==================================================

elif page == "Module 4 : AI Assistant":

    st.title("🤖 AI Maintenance Assistant")

    st.caption(
        "Analyze machine health using Local Llama 3.1 (Ollama)."
    )

    st.divider()

    st.subheader("Select Machine")

    machine_ids = sorted(df["Product ID"].astype(str).tolist())

    selected_machine = st.selectbox(
        "Choose Product ID",
        machine_ids
    )

    machine = df[
        df["Product ID"].astype(str) == selected_machine
    ].iloc[0]


    st.subheader("Machine Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Machine Type",
            machine["Type"]
        )

        st.metric(
            "Air Temperature",
            f'{machine["Air temperature [K]"]:.1f} K'
        )

        st.metric(
            "RPM",
            f'{machine["Rotational speed [rpm]"]:.0f}'
        )

    with col2:
        st.metric(
            "Torque",
            f'{machine["Torque [Nm]"]:.1f} Nm'
        )

        st.metric(
            "Tool Wear",
            f'{machine["Tool wear [min]"]:.0f} min'
        )

        status = (
            "Healthy"
            if machine["Machine failure"] == 0
            else "Failure"
        )

        st.metric(
            "Status",
            status
        )


    st.divider()

    generate_ai = st.button(
        "🤖 Generate AI Maintenance Report",
        use_container_width=True
    )

    if generate_ai:

        with st.spinner("🤖 AI is analyzing the machine. Please wait..."):

            prompt = f"""
    You are a Senior Industrial Predictive Maintenance Engineer with 20 years of experience.

    Your task is to analyze the following machine sensor readings and prepare a professional maintenance report.

    ==============================
    Machine Information
    ==============================

    Product ID: {selected_machine}

    Machine Type: {machine["Type"]}

    Report Date:
    {datetime.now().strftime("%d-%B-%Y %I:%M %p")}

    ==============================
    Sensor Readings
    ==============================

    Air Temperature:
    {machine["Air temperature [K]"]:.1f} K

    Process Temperature:
    {machine["Process temperature [K]"]:.1f} K

    Rotational Speed:
    {machine["Rotational speed [rpm]"]:.0f} RPM

    Torque:
    {machine["Torque [Nm]"]:.1f} Nm

    Tool Wear:
    {machine["Tool wear [min]"]:.0f} minutes

    ==============================
    Failure Indicators
    ==============================

    Tool Wear Failure:
    {"YES" if machine["TWF"] else "NO"}

    Heat Dissipation Failure:
    {"YES" if machine["HDF"] else "NO"}

    Power Failure:
    {"YES" if machine["PWF"] else "NO"}

    Overstrain Failure:
    {"YES" if machine["OSF"] else "NO"}

    Random Failure:
    {"YES" if machine["RNF"] else "NO"}

    Overall Machine Failure:
    {"YES" if machine["Machine failure"] else "NO"}

    ==============================
    Instructions
    ==============================

    Generate a professional maintenance report.

    Do NOT repeat:
    - Product ID
    - Machine Type
    - Report Date

    These are already displayed in the PDF header.

    Start directly from:

    1. Executive Summary

    2. Machine Health Summary

    3. Current Sensor Analysis

    4. Possible Risks

    5. Maintenance Recommendations

    6. Preventive Actions

    7. Risk Level (Low /Medium /High)

    8. Final Conclusion

    Rules:

    • Keep the report concise.

    • Use bullet points wherever appropriate.

    • Mention only meaningful observations.

    • Avoid unnecessary explanations.

    • Write professionally like an industrial maintenance engineer.

    """

            response = ollama.chat(
                model="llama3.1",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            ai_report = response["message"]["content"]

            report_lower = ai_report.lower()

            if "high" in report_lower:
                st.error("🔴 High Risk Machine")

            elif "medium" in report_lower:
                st.warning("🟡 Medium Risk Machine")

            else:
                st.success("🟢 Low Risk Machine")

            st.success("✅ AI Report Generated Successfully!")

            st.divider()

            st.subheader("🤖 AI Maintenance Report")

            st.markdown(ai_report)

            pdf_file = generate_pdf(
                ai_report,
                machine
            )

            st.info(f"💾 Report automatically saved to: {pdf_file}")

            with open(pdf_file, "rb") as pdf:

                st.download_button(

                    label="📄 Download AI Maintenance Report",

                    data=pdf,

                    file_name=os.path.basename(pdf_file),

                    mime="application/pdf",

                    use_container_width=True
                )

# ==================================================
# MODULE 5
# ==================================================

elif page == "Module 5 : Work Order Creation Console":

    st.title("🛠 Work Order Creation Console")

    st.caption(
        "Create and manage predictive maintenance work orders."
    )

    st.divider()

    tab1, tab2 = st.tabs(
        [
            "📋 Work Order Registry",
            "➕ Create Work Order"
        ]
    )

    st.write("")

    # ==================================================
    # TAB 1 - WORK ORDER REGISTRY
    # ==================================================

    with tab1:

        st.subheader("📋 Work Order Registry")

        conn = sqlite3.connect("maintenance.db")

        orders = pd.read_sql_query(
            """
            SELECT *
            FROM work_orders
            ORDER BY id DESC
            """,
            conn
        )

        conn.close()

        # ==================================================
        # CREATE DISPLAY WORK ORDER ID
        # ==================================================

        if not orders.empty:

            orders["WO_ID"] = orders["id"].apply(
                lambda x: f"WO-{int(x):04d}"
            )

        # ==================================================
        # WORK ORDER SUMMARY
        # ==================================================

        total_orders = len(orders)

        open_orders = len(
            orders[
                orders["status"] == "Open"
            ]
        )

        active_repairs = len(
            orders[
                orders["status"] == "In Progress"
            ]
        )

        completed_orders = len(
            orders[
                orders["status"] == "Completed"
            ]
        )

        st.subheader("📊 Work Order Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "📋 Total Work Orders",
                total_orders
            )

        with col2:

            st.metric(
                "🟠 Open Tasks",
                open_orders
            )

        with col3:

            st.metric(
                "🛠 Active Repairs",
                active_repairs
            )

        with col4:

            st.metric(
                "✅ Completed Repairs",
                completed_orders
            )

        st.divider()

        # ==================================================
        # WORK ORDER REGISTRY TABLE
        # ==================================================

        if orders.empty:

            st.info(
                "No work orders have been created yet."
            )

        else:

            registry_display = orders.copy()

            # Remove internal database ID
            registry_display = registry_display.drop(
                columns=["id"]
            )

            # Put WO_ID as first column
            columns = ["WO_ID"] + [
                col
                for col in registry_display.columns
                if col != "WO_ID"
            ]

            registry_display = registry_display[
                columns
            ]

            st.dataframe(
                registry_display,
                use_container_width=True,
                hide_index=True
            )

            # ==================================================
            # PDF EXPORT
            # ==================================================

            st.divider()

            st.subheader("📄 Export Work Order")

            pdf_col1, pdf_col2 = st.columns(
                [2, 1]
            )

            with pdf_col1:

                selected_wo = st.selectbox(
                    "Select Work Order",
                    orders["WO_ID"].tolist(),
                    key="module5_pdf_order"
                )

            selected_order = orders[
                orders["WO_ID"] == selected_wo
            ].iloc[0]

            with pdf_col2:

                st.write("")
                st.write("")

                pdf_data = generate_work_order_pdf(
                    selected_order
                )

                st.download_button(
                    label="📥 Download Work Order PDF",
                    data=pdf_data,
                    file_name=f"Work_Order_{selected_wo}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    # ==================================================
    # TAB 2 - CREATE WORK ORDER
    # ==================================================

    with tab2:

        st.subheader("➕ Create New Work Order")

        machine_ids = sorted(
            df["Product ID"].astype(str).tolist()
        )

        selected_machine = st.selectbox(
            "Select Product ID",
            machine_ids,
            key="work_order_machine"
        )

        selected_row = df[
            df["Product ID"].astype(str) == selected_machine
        ].iloc[0]

        st.text_input(
            "Machine Type",
            value=selected_row["Type"],
            disabled=True
        )

        technician = st.text_input(
            "Technician Name",
            placeholder="Enter Technician Name"
        )

        priority = st.selectbox(
            "Priority",
            [
                "Low",
                "Medium",
                "High"
            ]
        )

        maintenance_type = st.selectbox(
            "Maintenance Type",
            [
                "Preventive",
                "Corrective",
                "Emergency"
            ]
        )

        description = st.text_area(
            "Maintenance Description",
            placeholder="Describe the maintenance task, observations, and required repair..."
        )

        create_order = st.button(
            "🛠 Create Work Order",
            use_container_width=True
        )

        if create_order:

            if (
                technician.strip() == ""
                or
                description.strip() == ""
            ):

                st.error(
                    "Please enter Technician Name and Maintenance Description."
                )

            else:

                conn = sqlite3.connect(
                    "maintenance.db"
                )

                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO work_orders
                    (
                        product_id,
                        machine_type,
                        technician,
                        priority,
                        maintenance_type,
                        description,
                        status,
                        created_date
                    )

                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?)
                    """,

                    (
                        selected_machine,
                        selected_row["Type"],
                        technician,
                        priority,
                        maintenance_type,
                        description,
                        "Open",
                        datetime.now().strftime(
                            "%d-%m-%Y %H:%M"
                        )
                    )
                )

                conn.commit()

                order_id = cursor.lastrowid

                conn.close()

                display_order_id = (
                    f"WO-{int(order_id):04d}"
                )

                st.success(
                    f"✅ Work Order {display_order_id} created successfully!"
                )


# ==================================================
# MODULE 6: WORK ORDER MANAGEMENT
# ==================================================

elif page == "Module 6 : Work Order Management":

    st.title("🛠 Work Order Management")

    st.caption(
        "Manage, update and monitor all maintenance work orders."
    )

    st.divider()

    # ==================================================
    # LOAD WORK ORDERS
    # ==================================================

    conn = sqlite3.connect("maintenance.db")

    work_orders = pd.read_sql_query(
        """
        SELECT *
        FROM work_orders
        ORDER BY id DESC
        """,
        conn
    )

    conn.close()

    # ==================================================
    # HANDLE EMPTY DATABASE
    # ==================================================

    if work_orders.empty:

        st.info(
            "📋 No work orders have been created yet."
        )

        st.subheader("📊 Work Order Dashboard")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "📋 Total Work Orders",
                0
            )

        with col2:

            st.metric(
                "🟠 Open Work Orders",
                0
            )

        with col3:

            st.metric(
                "🛠 In Progress",
                0
            )

        with col4:

            st.metric(
                "✅ Completed",
                0
            )

    else:

        # ==================================================
        # CREATE DISPLAY WORK ORDER ID
        # ==================================================

        work_orders["WO_ID"] = work_orders["id"].apply(
            lambda x: f"WO-{int(x):04d}"
        )

        # ==================================================
        # WORK ORDER DASHBOARD
        # ==================================================

        st.subheader("📊 Work Order Dashboard")

        total_orders = len(work_orders)

        open_orders = len(
            work_orders[
                work_orders["status"] == "Open"
            ]
        )

        in_progress_orders = len(
            work_orders[
                work_orders["status"] == "In Progress"
            ]
        )

        completed_orders = len(
            work_orders[
                work_orders["status"] == "Completed"
            ]
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "📋 Total Work Orders",
                total_orders
            )

        with col2:

            st.metric(
                "🟠 Open Work Orders",
                open_orders
            )

        with col3:

            st.metric(
                "🛠 In Progress",
                in_progress_orders
            )

        with col4:

            st.metric(
                "✅ Completed",
                completed_orders
            )

        # ==================================================
        # SEARCH & FILTER
        # ==================================================

        st.divider()

        st.subheader(
            "🔍 Search & Filter Work Orders"
        )

        search_wo_col, search_product_col, status_col, priority_col = st.columns(
            [1.5, 1.5, 1, 1]
        )

        with search_wo_col:

            search_wo_id = st.text_input(
                "Search by Work Order ID",
                placeholder="e.g. WO-0001",
                key="module6_search_wo"
            )

        with search_product_col:

            search_product = st.text_input(
                "Search by Product ID",
                placeholder="e.g. L53112",
                key="module6_search_product"
            )

        with status_col:

            selected_status = st.selectbox(
                "Status",
                [
                    "All",
                    "Open",
                    "In Progress",
                    "Completed"
                ],
                key="module6_status_filter"
            )

        with priority_col:

            selected_priority = st.selectbox(
                "Priority",
                [
                    "All",
                    "High",
                    "Medium",
                    "Low"
                ],
                key="module6_priority_filter"
            )

        # ==================================================
        # APPLY SEARCH AND FILTERS
        # ==================================================

        filtered_orders = work_orders.copy()

        # --------------------------------------------------
        # Search by Work Order ID
        # --------------------------------------------------

        if search_wo_id.strip():

            filtered_orders = filtered_orders[
                filtered_orders["WO_ID"].str.contains(
                    search_wo_id.strip(),
                    case=False,
                    na=False
                )
            ]

        # --------------------------------------------------
        # Search by Product ID
        # --------------------------------------------------

        if search_product.strip():

            filtered_orders = filtered_orders[
                filtered_orders["product_id"]
                .astype(str)
                .str.contains(
                    search_product.strip(),
                    case=False,
                    na=False
                )
            ]

        # --------------------------------------------------
        # Filter by Status
        # --------------------------------------------------

        if selected_status != "All":

            filtered_orders = filtered_orders[
                filtered_orders["status"] == selected_status
            ]

        # --------------------------------------------------
        # Filter by Priority
        # --------------------------------------------------

        if selected_priority != "All":

            filtered_orders = filtered_orders[
                filtered_orders["priority"] == selected_priority
            ]

        # ==================================================
        # WORK ORDER LIST
        # ==================================================

        st.divider()

        st.subheader(
            "📋 Work Order List"
        )

        if filtered_orders.empty:

            st.warning(
                "No work orders found matching the selected filters."
            )

        else:

            display_orders = filtered_orders.copy()

            # Remove internal database ID
            display_orders = display_orders.drop(
                columns=["id"]
            )

            # Put WO_ID as first column
            columns = ["WO_ID"] + [
                col
                for col in display_orders.columns
                if col != "WO_ID"
            ]

            display_orders = display_orders[
                columns
            ]

            st.dataframe(
                display_orders,
                use_container_width=True,
                hide_index=True
            )

        # ==================================================
        # MANAGE WORK ORDER
        # ==================================================

        st.divider()

        st.subheader("🛠 Manage Work Order")

        st.caption(
            "Select a work order to view its details, update its status, "
            "or remove it from the maintenance registry."
        )

        if filtered_orders.empty:

            st.info(
                "📋 No work order is available for management."
            )

        else:

            # ==================================================
            # SELECT WORK ORDER
            # ==================================================

            management_wo = st.selectbox(
                "Select Work Order",
                filtered_orders["WO_ID"].tolist(),
                key="module6_manage_wo"
            )

            selected_work_order = filtered_orders[
                filtered_orders["WO_ID"] == management_wo
            ].iloc[0]


            # ==================================================
            # WORK ORDER DETAILS
            # ==================================================

            st.markdown("### 📄 Work Order Details")

            detail_col1, detail_col2, detail_col3 = st.columns(3)

            with detail_col1:

                st.write(
                    f"**Work Order ID:** {selected_work_order['WO_ID']}"
                )

                st.write(
                    f"**Product ID:** {selected_work_order['product_id']}"
                )

                st.write(
                    f"**Machine Type:** {selected_work_order['machine_type']}"
                )

            with detail_col2:

                st.write(
                    f"**Technician:** {selected_work_order['technician']}"
                )

                st.write(
                    f"**Priority:** {selected_work_order['priority']}"
                )

                st.write(
                    f"**Maintenance Type:** "
                    f"{selected_work_order['maintenance_type']}"
                )

            with detail_col3:

                st.write(
                    f"**Current Status:** {selected_work_order['status']}"
                )

                st.write(
                    f"**Created Date:** "
                    f"{selected_work_order['created_date']}"
                )

            st.write(
                f"**Description:** "
                f"{selected_work_order['description']}"
            )


            # ==================================================
            # WORK ORDER ACTIONS
            # ==================================================

            st.divider()

            st.subheader("⚙️ Work Order Actions")

            st.caption(
                "Update the maintenance status or remove this work order "
                "from the registry."
            )

            action_col1, action_col2 = st.columns(
                [1, 1],
                gap="large"
            )


            # ==================================================
            # UPDATE WORK ORDER CARD
            # ==================================================

            with action_col1:

                with st.container(border=True):

                    st.markdown(
                        "### 🔄 Update Work Order"
                    )

                    st.caption(
                        "Change the current maintenance status of this work order."
                    )

                    st.markdown(
                        f"""
                        **Selected Work Order**

                        `{selected_work_order["WO_ID"]}`
                        """
                    )

                    st.markdown(
                        f"""
                        **Current Status:** `{selected_work_order["status"]}`
                        """
                    )

                    st.write("")

                    current_status = selected_work_order["status"]

                    status_options = [
                        "Open",
                        "In Progress",
                        "Completed"
                    ]

                    new_status = st.selectbox(
                        "New Status",
                        status_options,
                        index=status_options.index(
                            current_status
                        ),
                        key=f"module6_new_status_{management_wo}"
                    )

                    if new_status == current_status:

                        st.info(
                            f"ℹ️ The work order is already "
                            f"marked as **{current_status}**."
                        )

                    else:

                        st.warning(
                            f"Status will change from "
                            f"**{current_status}** to **{new_status}**."
                        )

                    update_status = st.button(
                        "🔄 Update Status",
                        use_container_width=True,
                        key=f"module6_update_status_{management_wo}"
                    )

                    if update_status:

                        if new_status == current_status:

                            st.warning(
                                "⚠️ Please select a different status "
                                "before updating."
                            )

                        else:

                            conn = sqlite3.connect(
                                "maintenance.db"
                            )

                            cursor = conn.cursor()

                            cursor.execute(
                                """
                                UPDATE work_orders
                                SET status = ?
                                WHERE id = ?
                                """,
                                (
                                    new_status,
                                    int(selected_work_order["id"])
                                )
                            )

                            conn.commit()

                            conn.close()

                            st.success(
                                f"✅ {management_wo} status updated "
                                f"to **{new_status}**."
                            )

                            st.rerun()


            # ==================================================
            # DELETE WORK ORDER CARD
            # ==================================================

            with action_col2:

                with st.container(border=True):

                    st.markdown(
                        "### 🗑 Delete Work Order"
                    )

                    st.caption(
                        "Permanently remove this work order "
                        "from the database."
                    )

                    st.markdown(
                        f"""
                        **Selected Work Order**

                        `{selected_work_order["WO_ID"]}`
                        """
                    )

                    st.markdown(
                        f"""
                        **Product ID:** `{selected_work_order["product_id"]}`

                        **Current Status:** `{selected_work_order["status"]}`
                        """
                    )

                    st.write("")

                    st.warning(
                        "⚠️ This action cannot be undone."
                    )

                    delete_confirmation = st.checkbox(
                        "I understand that this work order "
                        "will be permanently deleted.",
                        key=f"module6_delete_confirmation_{management_wo}"
                    )

                    delete_order = st.button(
                        "🗑 Delete Work Order",
                        use_container_width=True,
                        key=f"module6_delete_order_{management_wo}"
                    )

                    if delete_order:

                        if not delete_confirmation:

                            st.error(
                                "❌ Please confirm the deletion "
                                "before proceeding."
                            )

                        else:

                            conn = sqlite3.connect(
                                "maintenance.db"
                            )

                            cursor = conn.cursor()

                            cursor.execute(
                                """
                                DELETE FROM work_orders
                                WHERE id = ?
                                """,
                                (
                                    int(selected_work_order["id"]),
                                )
                            )

                            conn.commit()

                            conn.close()

                            st.success(
                                f"🗑 {management_wo} deleted successfully."
                            )

                            st.rerun()


# ==================================================
# MODULE 7 : PREVENTIVE MAINTENANCE
# ==================================================

elif page == "Module 7 : Preventive Maintenance":

    st.title("📅 Preventive Maintenance")
    st.caption(
        "Plan, schedule, monitor and complete preventive maintenance activities."
    )

    st.divider()

    # ==================================================
    # LOAD PREVENTIVE MAINTENANCE DATA
    # ==================================================

    conn = sqlite3.connect("maintenance.db")

    pm_df = pd.read_sql_query(
        """
        SELECT *
        FROM preventive_maintenance
        ORDER BY id DESC
        """,
        conn
    )

    checklist_df = pd.read_sql_query(
        """
        SELECT *
        FROM maintenance_checklists
        """,
        conn
    )

    conn.close()

    # ==================================================
    # MAINTENANCE HISTORY TABLE
    # ==================================================

    conn = sqlite3.connect("maintenance.db")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance_history
        (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pm_id TEXT,
            product_id TEXT,
            machine_type TEXT,
            maintenance_type TEXT,
            frequency TEXT,
            technician TEXT,
            scheduled_date TEXT,
            completed_date TEXT,
            status TEXT,
            checklist_progress INTEGER,
            notes TEXT
        )
        """
    )

    conn.commit()
    conn.close()

    # ==================================================
    # AUTOMATIC OVERDUE STATUS UPDATE
    # ==================================================

    today = datetime.now().date()

    if not pm_df.empty:

        for _, pm in pm_df.iterrows():

            if (
                pm["status"] == "Scheduled"
                and pm["next_due_date"]
            ):

                try:

                    due_date = datetime.strptime(
                        pm["next_due_date"],
                        "%Y-%m-%d"
                    ).date()

                    if due_date < today:

                        conn = sqlite3.connect(
                            "maintenance.db"
                        )

                        cursor = conn.cursor()

                        cursor.execute(
                            """
                            UPDATE preventive_maintenance
                            SET status = 'Overdue'
                            WHERE id = ?
                            """,
                            (int(pm["id"]),)
                        )

                        conn.commit()
                        conn.close()

                except Exception:
                    pass

        # Reload after automatic status update

        conn = sqlite3.connect("maintenance.db")

        pm_df = pd.read_sql_query(
            """
            SELECT *
            FROM preventive_maintenance
            ORDER BY id DESC
            """,
            conn
        )

        conn.close()

    # ==================================================
    # KPI DASHBOARD
    # ==================================================

    st.subheader("📊 Preventive Maintenance Dashboard")

    total_pm = len(pm_df)

    scheduled_pm = len(
        pm_df[
            pm_df["status"] == "Scheduled"
        ]
    )

    in_progress_pm = len(
        pm_df[
            pm_df["status"] == "In Progress"
        ]
    )

    completed_pm = len(
        pm_df[
            pm_df["status"] == "Completed"
        ]
    )

    overdue_pm = len(
        pm_df[
            pm_df["status"] == "Overdue"
        ]
    )

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:

        st.metric(
            "📋 Total Schedules",
            total_pm
        )

    with kpi2:

        st.metric(
            "🟢 Scheduled",
            scheduled_pm
        )

    with kpi3:

        st.metric(
            "🛠 In Progress",
            in_progress_pm
        )

    with kpi4:

        st.metric(
            "✅ Completed",
            completed_pm
        )

    with kpi5:

        st.metric(
            "🔴 Overdue",
            overdue_pm
        )

    st.divider()

    # ==================================================
    # TABS
    # ==================================================

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📋 Maintenance Registry",
            "➕ Create Schedule",
            "📅 Upcoming & Overdue",
            "✅ Maintenance Checklist",
            "🤖 AI Recommendation",
            "📜 Maintenance History"
        ]
    )

    # ==================================================
    # TAB 1 : MAINTENANCE REGISTRY
    # ==================================================

    with tab1:

        st.subheader(
            "📋 Preventive Maintenance Registry"
        )

        if pm_df.empty:

            st.info(
                "No preventive maintenance schedules have been created yet."
            )

        else:

            display_pm = pm_df.copy()

            display_pm["PM_ID"] = display_pm["pm_id"]

            display_pm = display_pm[
                [
                    "PM_ID",
                    "product_id",
                    "machine_type",
                    "maintenance_type",
                    "frequency",
                    "start_date",
                    "next_due_date",
                    "technician",
                    "status",
                    "description"
                ]
            ]

            display_pm.columns = [
                "PM ID",
                "Product ID",
                "Machine Type",
                "Maintenance Type",
                "Frequency",
                "Start Date",
                "Next Due Date",
                "Technician",
                "Status",
                "Description"
            ]

            st.dataframe(
                display_pm,
                use_container_width=True,
                hide_index=True
            )

        st.divider()

        # --------------------------------------------------
        # STATUS CHART
        # --------------------------------------------------

        if not pm_df.empty:

            status_counts = (
                pm_df["status"]
                .value_counts()
                .reset_index()
            )

            status_counts.columns = [
                "Status",
                "Count"
            ]

            status_fig = px.bar(
                status_counts,
                x="Status",
                y="Count",
                color="Status",
                text="Count",
                title="Preventive Maintenance Status"
            )

            status_fig.update_traces(
                textposition="outside"
            )

            st.plotly_chart(
                status_fig,
                use_container_width=True
            )

    # ==================================================
    # TAB 2 : CREATE SCHEDULE
    # ==================================================

    with tab2:

        st.subheader(
            "➕ Create Preventive Maintenance Schedule"
        )

        machine_ids = sorted(
            df["Product ID"]
            .astype(str)
            .tolist()
        )

        selected_pm_machine = st.selectbox(
            "Select Product ID",
            machine_ids,
            key="module7_pm_machine"
        )

        selected_pm_row = df[
            df["Product ID"].astype(str)
            == selected_pm_machine
        ].iloc[0]

        st.write(
            f"**Machine Type:** {selected_pm_row['Type']}"
        )

        st.divider()

        pm_col1, pm_col2 = st.columns(2)

        with pm_col1:

            pm_technician = st.text_input(
                "Technician Name",
                placeholder="Enter technician name",
                key="module7_pm_technician"
            )

            pm_maintenance_type = st.selectbox(
                "Maintenance Type",
                [
                    "Routine Inspection",
                    "Lubrication",
                    "Tool Replacement",
                    "Temperature Inspection",
                    "Mechanical Inspection",
                    "Electrical Inspection",
                    "Full Preventive Maintenance"
                ],
                key="module7_pm_type"
            )

            pm_frequency = st.selectbox(
                "Maintenance Frequency",
                [
                    "Daily",
                    "Weekly",
                    "Monthly",
                    "Quarterly",
                    "Every 6 Months",
                    "Yearly"
                ],
                key="module7_pm_frequency"
            )

        with pm_col2:

            pm_start_date = st.date_input(
                "Maintenance Start Date",
                value=datetime.now().date(),
                key="module7_pm_start"
            )

            pm_description = st.text_area(
                "Maintenance Description",
                placeholder=(
                    "Describe the preventive maintenance activity..."
                ),
                key="module7_pm_description"
            )

        create_pm = st.button(
            "📅 Create Maintenance Schedule",
            use_container_width=True,
            key="module7_create_pm"
        )

        if create_pm:

            if pm_technician.strip() == "":

                st.error(
                    "Please enter Technician Name."
                )

            elif pm_description.strip() == "":

                st.error(
                    "Please enter Maintenance Description."
                )

            else:

                # --------------------------------------------------
                # CALCULATE NEXT DUE DATE
                # --------------------------------------------------

                next_due = calculate_next_maintenance_date(
                    pm_start_date,
                    pm_frequency
                )
                
                # --------------------------------------------------
                # CREATE PM ID
                # --------------------------------------------------

                conn = sqlite3.connect(
                    "maintenance.db"
                )

                cursor = conn.cursor()

                pm_id = generate_next_pm_id(cursor)

                # --------------------------------------------------
                # INSERT PM
                # --------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO preventive_maintenance
                    (
                        pm_id,
                        product_id,
                        machine_type,
                        maintenance_type,
                        frequency,
                        start_date,
                        next_due_date,
                        technician,
                        status,
                        description,
                        created_date
                    )
                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pm_id,
                        selected_pm_machine,
                        selected_pm_row["Type"],
                        pm_maintenance_type,
                        pm_frequency,
                        pm_start_date.strftime(
                            "%Y-%m-%d"
                        ),
                        next_due.strftime(
                            "%Y-%m-%d"
                        ),
                        pm_technician,
                        "Scheduled",
                        pm_description,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )

                # --------------------------------------------------
                # CREATE CHECKLIST
                # --------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO maintenance_checklists
                    (
                        pm_id,
                        inspect_machine,
                        check_temperature,
                        check_rotational_speed,
                        check_torque,
                        inspect_tool_wear,
                        verify_machine_condition,
                        completion_percentage,
                        updated_date
                    )
                    VALUES
                    (?, 0, 0, 0, 0, 0, 0, 0, ?)
                    """,
                    (
                        pm_id,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    f"✅ Preventive Maintenance {pm_id} created successfully!"
                )

                st.rerun()

    # ==================================================
    # TAB 3 : UPCOMING & OVERDUE
    # ==================================================

    with tab3:

        st.subheader(
            "📅 Upcoming & Overdue Maintenance"
        )

        if pm_df.empty:

            st.info(
                "No maintenance schedules available."
            )

        else:

            upcoming_df = pm_df[
                pm_df["status"].isin(
                    [
                        "Scheduled",
                        "Overdue"
                    ]
                )
            ].copy()

            if upcoming_df.empty:

                st.success(
                    "🎉 No upcoming or overdue maintenance."
                )

            else:

                upcoming_df["Due Date"] = pd.to_datetime(
                    upcoming_df["next_due_date"],
                    errors="coerce"
                )

                upcoming_df["Days Remaining"] = (
                    upcoming_df["Due Date"]
                    - pd.Timestamp.now().normalize()
                ).dt.days

                upcoming_df["Priority"] = upcoming_df[
                    "Days Remaining"
                ].apply(
                    lambda x:
                    "🔴 Overdue"
                    if x < 0
                    else
                    "🟡 Due Soon"
                    if x <= 7
                    else
                    "🟢 Upcoming"
                )

                upcoming_display = upcoming_df[
                    [
                        "pm_id",
                        "product_id",
                        "machine_type",
                        "maintenance_type",
                        "technician",
                        "next_due_date",
                        "Days Remaining",
                        "Priority",
                        "status"
                    ]
                ].copy()

                upcoming_display.columns = [
                    "PM ID",
                    "Product ID",
                    "Machine Type",
                    "Maintenance Type",
                    "Technician",
                    "Next Due Date",
                    "Days Remaining",
                    "Priority",
                    "Status"
                ]

                st.dataframe(
                    upcoming_display,
                    use_container_width=True,
                    hide_index=True
                )
                
                # ==================================================
                # MAINTENANCE CALENDAR
                # ==================================================

                st.divider()

                st.subheader("🗓️ Maintenance Calendar")

                st.caption(
                    "Monthly calendar showing scheduled, overdue and completed "
                    "preventive maintenance activities."
                )

                # --------------------------------------------------
                # SELECT MONTH
                # --------------------------------------------------

                calendar_col1, calendar_col2 = st.columns([1, 3])

                with calendar_col1:

                    calendar_month = st.date_input(
                        "Select Month",
                        value=datetime.now().date(),
                        key="module7_calendar_month"
                    )

                selected_year = calendar_month.year
                selected_month = calendar_month.month

                month_name = calendar.month_name[selected_month]

                with calendar_col2:

                    st.markdown(
                        f"""
                        <div style="
                            padding: 12px 18px;
                            margin-top: 28px;
                            border-radius: 8px;
                            background-color: #161b22;
                            border: 1px solid #30363d;
                        ">
                            <h3 style="margin:0;">
                                📅 {month_name} {selected_year}
                            </h3>
                            <p style="margin:5px 0 0 0; color:#9ca3af;">
                                Preventive Maintenance Schedule
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # --------------------------------------------------
                # LOAD CALENDAR DATA
                # --------------------------------------------------

                conn = sqlite3.connect("maintenance.db")

                calendar_pm_df = pd.read_sql_query(
                    """
                    SELECT
                        pm_id,
                        product_id,
                        machine_type,
                        maintenance_type,
                        frequency,
                        next_due_date,
                        technician,
                        status
                    FROM preventive_maintenance
                    WHERE status IN ('Scheduled', 'Overdue')
                    """,
                    conn
                )

                calendar_history_df = pd.read_sql_query(
                    """
                    SELECT
                        pm_id,
                        product_id,
                        machine_type,
                        maintenance_type,
                        technician,
                        completed_date,
                        status
                    FROM maintenance_history
                    WHERE status = 'Completed'
                    """,
                    conn
                )

                conn.close()

                # --------------------------------------------------
                # PREPARE CALENDAR EVENTS
                # --------------------------------------------------

                calendar_events = []

                # Active preventive maintenance
                if not calendar_pm_df.empty:

                    for _, row in calendar_pm_df.iterrows():

                        try:

                            event_date = datetime.strptime(
                                str(row["next_due_date"]),
                                "%Y-%m-%d"
                            ).date()

                            calendar_events.append(
                                {
                                    "date": event_date,
                                    "pm_id": row["pm_id"],
                                    "product_id": row["product_id"],
                                    "maintenance_type": row[
                                        "maintenance_type"
                                    ],
                                    "technician": row["technician"],
                                    "status": row["status"]
                                }
                            )

                        except Exception:
                            pass

                # Completed maintenance history
                if not calendar_history_df.empty:

                    for _, row in calendar_history_df.iterrows():

                        try:

                            event_date = datetime.strptime(
                                str(row["completed_date"]),
                                "%Y-%m-%d"
                            ).date()

                            calendar_events.append(
                                {
                                    "date": event_date,
                                    "pm_id": row["pm_id"],
                                    "product_id": row["product_id"],
                                    "maintenance_type": row[
                                        "maintenance_type"
                                    ],
                                    "technician": row["technician"],
                                    "status": "Completed"
                                }
                            )

                        except Exception:
                            pass

                # --------------------------------------------------
                # CALENDAR LEGEND
                # --------------------------------------------------

                st.html(
                    """
                    <div style="
                        display:flex;
                        gap:25px;
                        flex-wrap:wrap;
                        margin:15px 0;
                        padding:12px 16px;
                        border-radius:8px;
                        background:#161b22;
                        border:1px solid #30363d;
                        color:#f0f6fc;
                        font-size:14px;
                    ">
                        <span>🟢 <b>Scheduled</b></span>
                        <span>🔴 <b>Overdue</b></span>
                        <span>🔵 <b>Completed</b></span>
                    </div>
                    """
                )

                # --------------------------------------------------
                # CALENDAR HEADER
                # --------------------------------------------------

                weekday_names = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday"
                ]

                header_columns = st.columns(7)

                for i, day_name in enumerate(weekday_names):

                    with header_columns[i]:

                        st.html(
                            f"""
                            <div style="
                                text-align:center;
                                font-weight:bold;
                                padding:10px 4px;
                                background:#21262d;
                                border:1px solid #30363d;
                                border-radius:6px;
                                margin-bottom:4px;
                                color:#f0f6fc;
                            ">
                                {day_name[:3]}
                            </div>
                            """
                        )

                # --------------------------------------------------
                # GENERATE MONTH CALENDAR
                # --------------------------------------------------

                month_calendar = calendar.monthcalendar(
                    selected_year,
                    selected_month
                )

                for week in month_calendar:

                    week_columns = st.columns(7)

                    for day_index, day_number in enumerate(week):

                        with week_columns[day_index]:

                            # Empty calendar cell
                            if day_number == 0:

                                st.html(
                                    """
                                    <div style="
                                        min-height:120px;
                                        border:1px solid #21262d;
                                        border-radius:6px;
                                        margin-bottom:5px;
                                        background:#0d1117;
                                    ">
                                    </div>
                                    """
                                )

                                continue

                            current_calendar_date = datetime(
                                selected_year,
                                selected_month,
                                day_number
                            ).date()

                            # ------------------------------------------
                            # FIND EVENTS FOR THIS DATE
                            # ------------------------------------------

                            day_events = [
                                event
                                for event in calendar_events
                                if event["date"] == current_calendar_date
                            ]

                            # --------------------------------------------------
                            # DAY CELL
                            # --------------------------------------------------

                            if current_calendar_date == today:

                                border_style = "2px solid #58a6ff"
                                background_style = "#172b45"

                            else:

                                border_style = "1px solid #30363d"
                                background_style = "#0d1117"


                            # --------------------------------------------------
                            # BUILD EVENTS HTML
                            # --------------------------------------------------

                            event_html = ""

                            for event in day_events:

                                if event["status"] == "Scheduled":

                                    badge_color = "#1f9d55"
                                    badge_icon = "🟢"

                                elif event["status"] == "Overdue":

                                    badge_color = "#dc3545"
                                    badge_icon = "🔴"

                                else:

                                    badge_color = "#2563eb"
                                    badge_icon = "🔵"

                                event_html += f"""
                                    <div style="
                                        margin-top:5px;
                                        padding:5px;
                                        border-radius:5px;
                                        background:{badge_color};
                                        color:white;
                                        font-size:11px;
                                        line-height:1.3;
                                    ">
                                        {badge_icon}
                                        <b>{event["pm_id"]}</b><br>
                                        {event["product_id"]}<br>
                                        {event["technician"]}
                                    </div>
                                """


                            # --------------------------------------------------
                            # RENDER DAY CELL
                            # --------------------------------------------------

                            day_html = f"""
                            <div style="
                                min-height:120px;
                                padding:7px;
                                border:{border_style};
                                border-radius:6px;
                                margin-bottom:5px;
                                background:{background_style};
                                color:#f0f6fc;
                                box-sizing:border-box;
                            ">

                                <div style="
                                    font-weight:bold;
                                    font-size:15px;
                                    margin-bottom:4px;
                                ">
                                    {day_number}
                                </div>

                                {event_html}

                            </div>
                            """

                            st.html(day_html)

                # --------------------------------------------------
                # SELECTED DATE DETAILS
                # --------------------------------------------------

                st.divider()

                st.subheader("📋 Calendar Event Details")

                month_events = [
                    event
                    for event in calendar_events
                    if (
                        event["date"].year == selected_year
                        and event["date"].month == selected_month
                    )
                ]

                if month_events:

                    calendar_details_df = pd.DataFrame(
                        month_events
                    )

                    calendar_details_df["Date"] = (
                        calendar_details_df["date"]
                        .apply(
                            lambda x: x.strftime("%d-%m-%Y")
                        )
                    )

                    calendar_details_df = calendar_details_df[
                        [
                            "Date",
                            "pm_id",
                            "product_id",
                            "maintenance_type",
                            "technician",
                            "status"
                        ]
                    ]

                    calendar_details_df.columns = [
                        "Date",
                        "PM ID",
                        "Product ID",
                        "Maintenance Type",
                        "Technician",
                        "Status"
                    ]

                    calendar_details_df = (
                        calendar_details_df
                        .sort_values("Date")
                    )

                    st.dataframe(
                        calendar_details_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        f"📅 No maintenance activities found "
                        f"for {month_name} {selected_year}."
                    )

                # ==================================================
                # CREATE PREVENTIVE MAINTENANCE WORK ORDER
                # ==================================================

                st.divider()

                st.subheader(
                    "🛠 Create Maintenance Work Order"
                )

                st.caption(
                    "Create a work order directly from a preventive maintenance schedule."
                )

                pm_work_order = st.selectbox(
                    "Select Preventive Maintenance Schedule",
                    pm_df["pm_id"].tolist(),
                    key="module7_work_order_pm"
                )

                selected_pm_wo = pm_df[
                    pm_df["pm_id"] == pm_work_order
                ].iloc[0]

                wo_col1, wo_col2 = st.columns(2)

                with wo_col1:

                    st.write(
                        f"**Product ID:** {selected_pm_wo['product_id']}"
                    )

                    st.write(
                        f"**Machine Type:** {selected_pm_wo['machine_type']}"
                    )

                    st.write(
                        f"**Maintenance Type:** "
                        f"{selected_pm_wo['maintenance_type']}"
                    )

                with wo_col2:

                    st.write(
                        f"**Technician:** "
                        f"{selected_pm_wo['technician']}"
                    )

                    st.write(
                        f"**Priority:** "
                        f"{'High' if selected_pm_wo['status'] == 'Overdue' else 'Medium'}"
                    )

                    st.write(
                        f"**Current PM Status:** "
                        f"{selected_pm_wo['status']}"
                    )

                create_pm_work_order = st.button(
                    "🛠 Create Work Order from Preventive Maintenance",
                    use_container_width=True,
                    key="module7_create_work_order"
                )

                if create_pm_work_order:

                    # --------------------------------------------------
                    # DETERMINE PRIORITY
                    # --------------------------------------------------

                    if selected_pm_wo["status"] == "Overdue":

                        wo_priority = "High"

                    else:

                        wo_priority = "Medium"

                    # --------------------------------------------------
                    # CHECK WHETHER WORK ORDER ALREADY EXISTS
                    # --------------------------------------------------

                    conn = sqlite3.connect(
                        "maintenance.db"
                    )

                    existing_wo = pd.read_sql_query(
                        """
                        SELECT *
                        FROM work_orders
                        WHERE product_id = ?
                        AND description LIKE ?
                        AND status != 'Completed'
                        """,
                        conn,
                        params=(
                            selected_pm_wo["product_id"],
                            f"%{selected_pm_wo['pm_id']}%"
                        )
                    )

                    if not existing_wo.empty:

                        conn.close()

                        st.warning(
                            f"⚠️ An active work order already exists "
                            f"for {selected_pm_wo['pm_id']}."
                        )

                    else:

                        cursor = conn.cursor()

                        # --------------------------------------------------
                        # CREATE WORK ORDER
                        # --------------------------------------------------

                        work_order_description = (
                            f"Preventive Maintenance {selected_pm_wo['pm_id']} | "
                            f"{selected_pm_wo['maintenance_type']} | "
                            f"{selected_pm_wo['description']}"
                        )

                        cursor.execute(
                            """
                            INSERT INTO work_orders
                            (
                                product_id,
                                machine_type,
                                technician,
                                priority,
                                maintenance_type,
                                description,
                                status,
                                created_date
                            )
                            VALUES
                            (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                selected_pm_wo["product_id"],
                                selected_pm_wo["machine_type"],
                                selected_pm_wo["technician"],
                                wo_priority,
                                selected_pm_wo["maintenance_type"],
                                work_order_description,
                                "Open",
                                datetime.now().strftime(
                                    "%d-%m-%Y %H:%M"
                                )
                            )
                        )

                        conn.commit()

                        work_order_id = cursor.lastrowid

                        conn.close()

                        display_wo_id = (
                            f"WO-{int(work_order_id):04d}"
                        )

                        st.success(
                            f"✅ Work Order {display_wo_id} created successfully "
                            f"from {selected_pm_wo['pm_id']}."
                        )

                        st.info(
                            "You can manage this work order from "
                            "**Module 6 : Work Order Management**."
                        )

    # ==================================================
    # TAB 4 : MAINTENANCE CHECKLIST
    # ==================================================

    with tab4:

        st.subheader(
            "✅ Maintenance Checklist"
        )

        if pm_df.empty:

            st.info(
                "No preventive maintenance schedules available."
            )

        else:

            selected_checklist_pm = st.selectbox(
                "Select Maintenance Schedule",
                pm_df["pm_id"].tolist(),
                key="module7_checklist_pm"
            )

            checklist_pm = pm_df[
                pm_df["pm_id"] == selected_checklist_pm
            ].iloc[0]

            st.markdown(
                f"""
                **Product ID:** {checklist_pm['product_id']}  
                **Maintenance Type:** {checklist_pm['maintenance_type']}  
                **Technician:** {checklist_pm['technician']}  
                **Next Due Date:** {checklist_pm['next_due_date']}  
                **Current Status:** {checklist_pm['status']}
                """
            )

            st.divider()

            st.markdown(
                "### 🔍 Maintenance Inspection Checklist"
            )

            chk1 = st.checkbox(
                "Inspect machine condition",
                key="chk_machine_condition"
            )

            chk2 = st.checkbox(
                "Check operating temperature",
                key="chk_temperature"
            )

            chk3 = st.checkbox(
                "Check rotational speed",
                key="chk_rpm"
            )

            chk4 = st.checkbox(
                "Check torque condition",
                key="chk_torque"
            )

            chk5 = st.checkbox(
                "Inspect tool wear",
                key="chk_tool_wear"
            )

            chk6 = st.checkbox(
                "Verify overall machine condition",
                key="chk_overall_condition"
            )

            checklist_progress = int(
                (
                    sum(
                        [
                            chk1,
                            chk2,
                            chk3,
                            chk4,
                            chk5,
                            chk6
                        ]
                    ) / 6
                ) * 100
            )

            st.progress(
                checklist_progress / 100
            )

            st.write(
                f"**Checklist Progress: {checklist_progress}%**"
            )

            maintenance_notes = st.text_area(
                "Maintenance Notes",
                placeholder=(
                    "Enter observations, repairs performed, "
                    "parts replaced, machine condition, etc."
                ),
                key="module7_maintenance_notes"
            )

            complete_maintenance = st.button(
                "✅ Complete Maintenance",
                use_container_width=True,
                type="primary",
                key="module7_complete_maintenance"
            )

            if complete_maintenance:

                if checklist_progress < 100:

                    st.warning(
                        "⚠️ Please complete all checklist items "
                        "before marking the maintenance as completed."
                    )

                else:

                    completed_date = datetime.now().date()

                    # ==================================================
                    # CALCULATE NEXT MAINTENANCE DATE
                    # ==================================================

                    next_date = calculate_next_maintenance_date(
                        completed_date,
                        checklist_pm["frequency"]
                    )

                    # ==================================================
                    # CONNECT DATABASE
                    # ==================================================

                    conn = sqlite3.connect(
                        "maintenance.db"
                    )

                    cursor = conn.cursor()

                    # ==================================================
                    # SAVE MAINTENANCE HISTORY
                    # ==================================================

                    cursor.execute(
                        """
                        INSERT INTO maintenance_history
                        (
                            pm_id,
                            product_id,
                            machine_type,
                            maintenance_type,
                            frequency,
                            technician,
                            scheduled_date,
                            completed_date,
                            status,
                            checklist_progress,
                            notes
                        )
                        VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            checklist_pm["pm_id"],
                            checklist_pm["product_id"],
                            checklist_pm["machine_type"],
                            checklist_pm["maintenance_type"],
                            checklist_pm["frequency"],
                            checklist_pm["technician"],
                            checklist_pm["next_due_date"],
                            completed_date.strftime(
                                "%Y-%m-%d"
                            ),
                            "Completed",
                            checklist_progress,
                            maintenance_notes
                        )
                    )

                    # ==================================================
                    # UPDATE CURRENT PM STATUS
                    # ==================================================

                    cursor.execute(
                        """
                        UPDATE preventive_maintenance
                        SET status = 'Completed'
                        WHERE pm_id = ?
                        """,
                        (
                            checklist_pm["pm_id"],
                        )
                    )

                    # ==================================================
                    # CREATE NEXT PREVENTIVE MAINTENANCE SCHEDULE
                    # ==================================================

                    next_pm_id = generate_next_pm_id(cursor)

                    cursor.execute(
                        """
                        INSERT INTO preventive_maintenance
                        (
                            pm_id,
                            product_id,
                            machine_type,
                            maintenance_type,
                            frequency,
                            start_date,
                            next_due_date,
                            technician,
                            status,
                            description,
                            created_date
                        )
                        VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            next_pm_id,
                            checklist_pm["product_id"],
                            checklist_pm["machine_type"],
                            checklist_pm["maintenance_type"],
                            checklist_pm["frequency"],
                            completed_date.strftime("%Y-%m-%d"),
                            next_date.strftime("%Y-%m-%d"),
                            checklist_pm["technician"],
                            "Scheduled",
                            checklist_pm["description"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                    )

                    # ==================================================
                    # SAVE CHECKLIST PROGRESS
                    # ==================================================

                    cursor.execute(
                        """
                        UPDATE maintenance_checklists
                        SET
                            inspect_machine = ?,
                            check_temperature = ?,
                            check_rotational_speed = ?,
                            check_torque = ?,
                            inspect_tool_wear = ?,
                            verify_machine_condition = ?,
                            completion_percentage = ?,
                            updated_date = ?
                        WHERE pm_id = ?
                        """,
                        (
                            int(chk1),
                            int(chk2),
                            int(chk3),
                            int(chk4),
                            int(chk5),
                            int(chk6),
                            checklist_progress,
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            checklist_pm["pm_id"]
                        )
                    )

                    # ==================================================
                    # COMMIT CHANGES
                    # ==================================================

                    conn.commit()
                    conn.close()

                    # ==================================================
                    # SUCCESS MESSAGE
                    # ==================================================

                    st.success(
                        "✅ Maintenance completed successfully!"
                    )

                    st.info(
                        f"📋 Maintenance History saved for "
                        f"**{checklist_pm['pm_id']}**."
                    )

                    st.info(
                        f"📅 Next maintenance scheduled for "
                        f"**{next_date.strftime('%d-%m-%Y')}**."
                    )

                    st.success(
                        f"🆕 Next PM Schedule created: "
                        f"**{next_pm_id}**"
                    )

                    st.rerun()

    # ==================================================
    # TAB 5 : AI RECOMMENDATION
    # ==================================================

    with tab5:

        st.subheader(
            "🤖 AI Preventive Maintenance Recommendation"
        )

        if pm_df.empty:

            st.info(
                "Create a preventive maintenance schedule first."
            )

        else:

            ai_pm_id = st.selectbox(
                "Select Maintenance Schedule",
                pm_df["pm_id"].tolist(),
                key="module7_ai_pm"
            )

            ai_pm = pm_df[
                pm_df["pm_id"] == ai_pm_id
            ].iloc[0]

            ai_machine = df[
                df["Product ID"].astype(str)
                == str(ai_pm["product_id"])
            ]

            if ai_machine.empty:

                st.error(
                    "Machine information not found."
                )

            else:

                ai_machine = ai_machine.iloc[0]

                st.write(
                    f"**Product ID:** {ai_pm['product_id']}"
                )

                st.write(
                    f"**Maintenance Type:** "
                    f"{ai_pm['maintenance_type']}"
                )

                st.write(
                    f"**Frequency:** {ai_pm['frequency']}"
                )

                generate_recommendation = st.button(
                    "🤖 Generate AI Recommendation",
                    use_container_width=True,
                    key="module7_ai_button"
                )

                if generate_recommendation:

                    with st.spinner(
                        "🤖 AI is analyzing machine condition..."
                    ):

                        ai_prompt = f"""

You are a Senior Industrial Predictive Maintenance Engineer.

Analyze this machine and provide a preventive maintenance recommendation.

Machine Information
-------------------

Product ID:
{ai_pm["product_id"]}

Machine Type:
{ai_pm["machine_type"]}

Maintenance Type:
{ai_pm["maintenance_type"]}

Maintenance Frequency:
{ai_pm["frequency"]}

Sensor Readings
---------------

Air Temperature:
{ai_machine["Air temperature [K]"]:.1f} K

Process Temperature:
{ai_machine["Process temperature [K]"]:.1f} K

Rotational Speed:
{ai_machine["Rotational speed [rpm]"]:.0f} RPM

Torque:
{ai_machine["Torque [Nm]"]:.1f} Nm

Tool Wear:
{ai_machine["Tool wear [min]"]:.0f} minutes

Failure Indicators
-------------------

Tool Wear Failure:
{"YES" if ai_machine["TWF"] else "NO"}

Heat Dissipation Failure:
{"YES" if ai_machine["HDF"] else "NO"}

Power Failure:
{"YES" if ai_machine["PWF"] else "NO"}

Overstrain Failure:
{"YES" if ai_machine["OSF"] else "NO"}

Random Failure:
{"YES" if ai_machine["RNF"] else "NO"}

Overall Machine Failure:
{"YES" if ai_machine["Machine failure"] else "NO"}

Prepare a concise professional preventive maintenance recommendation.

Include:

1. Current Machine Condition
2. Maintenance Priority
3. Recommended Maintenance Actions
4. Sensor Parameters to Monitor
5. Potential Failure Risks
6. Technician Instructions
7. Final Recommendation

Do not invent sensor readings.
Base the recommendation only on the provided information.
"""

                        response = ollama.chat(
                            model="llama3.1",
                            messages=[
                                {
                                    "role": "user",
                                    "content": ai_prompt
                                }
                            ]
                        )

                        ai_recommendation = (
                            response["message"]["content"]
                        )

                        st.success(
                            "✅ AI Recommendation Generated"
                        )

                        # ==================================================
                        # DISPLAY AI RECOMMENDATION
                        # ==================================================

                        st.markdown(
                            ai_recommendation
                        )

                        # ==================================================
                        # DOWNLOAD AI GENERATED REPORT
                        # ==================================================

                        ai_report = f"""
                        MACHINE PREDICTIVE MAINTENANCE SYSTEM
                        AI-BASED PREVENTIVE MAINTENANCE REPORT
                        ==================================================

                        Product ID:
                        {ai_pm["product_id"]}

                        Machine Type:
                        {ai_pm["machine_type"]}

                        Maintenance Type:
                        {ai_pm["maintenance_type"]}

                        Maintenance Frequency:
                        {ai_pm["frequency"]}

                        Technician:
                        {ai_pm["technician"]}

                        Report Generated On:
                        {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

                        ==================================================
                        AI MAINTENANCE RECOMMENDATION
                        ==================================================

                        {ai_recommendation}

                        ==================================================
                        END OF REPORT
                        ==================================================
                        """

                        st.download_button(
                            label="📥 Download AI Maintenance Report",
                            data=ai_report,
                            file_name=f"AI_Maintenance_Report_{ai_pm['product_id']}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

    # ==================================================
    # TAB 6 : MAINTENANCE HISTORY
    # ==================================================

    with tab6:

        st.subheader(
            "📜 Maintenance History"
        )

        st.caption(
            "Historical record of completed preventive maintenance activities."
        )

        # ==================================================
        # LOAD MAINTENANCE HISTORY
        # ==================================================

        conn = sqlite3.connect(
            "maintenance.db"
        )

        history_df = pd.read_sql_query(
            """
            SELECT *
            FROM maintenance_history
            ORDER BY history_id DESC
            """,
            conn
        )

        conn.close()

        # ==================================================
        # CHECK HISTORY
        # ==================================================

        if history_df.empty:

            st.info(
                "No completed maintenance activities found."
            )

        else:

            # ==================================================
            # HISTORY SUMMARY
            # ==================================================

            total_history = len(
                history_df
            )

            completed_history = len(
                history_df[
                    history_df["status"] == "Completed"
                ]
            )

            avg_checklist = (
                history_df["checklist_progress"]
                .mean()
            )

            history_col1, history_col2, history_col3 = st.columns(3)

            with history_col1:

                st.metric(
                    "📜 Total Maintenance Records",
                    total_history
                )

            with history_col2:

                st.metric(
                    "✅ Completed Maintenance",
                    completed_history
                )

            with history_col3:

                st.metric(
                    "📊 Average Checklist Completion",
                    f"{avg_checklist:.1f}%"
                )

            st.divider()

            # ==================================================
            # HISTORY TABLE
            # ==================================================

            history_display = history_df.copy()

            history_display.columns = [
                "History ID",
                "PM ID",
                "Product ID",
                "Machine Type",
                "Maintenance Type",
                "Frequency",
                "Technician",
                "Scheduled Date",
                "Completed Date",
                "Status",
                "Checklist Progress",
                "Notes"
            ]

            st.dataframe(
                history_display,
                use_container_width=True,
                hide_index=True
            )
