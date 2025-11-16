"""
Streamlit page showing data insights and visualizations.
Demonstrates the relationship between income and graduation rates.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_engineering import build_featured_college_df


def main():
    """Main Streamlit app function for data insights."""

    # Page configuration
    st.set_page_config(
        page_title="Data Insights - Income & Graduation",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Title and description
    st.title("📊 Data Insights: Income & Educational Equity")

    st.markdown("""
    ## Why EquiPath Exists

    This page demonstrates the critical relationship between **family income** and **college graduation rates**.
    The data shows that students from low-income backgrounds face significant barriers to completing their degrees.

    **EquiPath was created to address this equity gap** by helping students find colleges where they're more likely to succeed.
    """)

    st.divider()

    # Load data
    with st.spinner("Loading college data..."):
        if 'insights_data' not in st.session_state:
            df = build_featured_college_df()
            st.session_state.insights_data = df
        else:
            df = st.session_state.insights_data

    # Key metrics at the top
    st.subheader("📈 Key Statistics")

    col1, col2, col3 = st.columns(3)

    # Calculate statistics
    pell_col = 'Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants'
    grad_col = "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"

    # Convert to numeric
    df[pell_col] = pd.to_numeric(df[pell_col], errors='coerce')
    df[grad_col] = pd.to_numeric(df[grad_col], errors='coerce')

    # Filter valid data
    valid_data = df[[pell_col, grad_col]].dropna()

    # Create income categories based on Pell Grant percentage
    # Higher Pell % = more low-income students
    valid_data['Income_Category'] = pd.cut(
        valid_data[pell_col],
        bins=[0, 25, 50, 75, 100],
        labels=['Higher Income (0-25% Pell)', 'Middle Income (25-50% Pell)',
                'Lower Income (50-75% Pell)', 'Lowest Income (75-100% Pell)']
    )

    # Calculate average graduation rates by income category
    grad_by_income = valid_data.groupby('Income_Category')[grad_col].mean()

    with col1:
        highest_income_grad = grad_by_income.iloc[0] if len(grad_by_income) > 0 else 0
        st.metric(
            "Higher Income Students",
            f"{highest_income_grad:.1f}%",
            delta="Graduation Rate",
            help="Average 6-year graduation rate at schools with 0-25% Pell Grant students"
        )

    with col2:
        lowest_income_grad = grad_by_income.iloc[-1] if len(grad_by_income) > 0 else 0
        st.metric(
            "Lowest Income Students",
            f"{lowest_income_grad:.1f}%",
            delta=f"{lowest_income_grad - highest_income_grad:.1f}% gap",
            delta_color="inverse",
            help="Average 6-year graduation rate at schools with 75-100% Pell Grant students"
        )

    with col3:
        gap = highest_income_grad - lowest_income_grad
        st.metric(
            "Graduation Gap",
            f"{gap:.1f}%",
            delta="Lower for low-income",
            delta_color="inverse",
            help="Difference in graduation rates between highest and lowest income student populations"
        )

    st.divider()

    # Visualization 1: Bar chart showing graduation rates by income level
    st.subheader("🎓 Graduation Rates by Student Income Level")

    st.markdown("""
    This chart shows that **schools serving more low-income students (higher % Pell Grant recipients)
    have lower graduation rates on average**. This highlights the need for tools like EquiPath to help
    students find institutions where they're most likely to succeed.
    """)

    # Create bar chart
    grad_by_income_df = grad_by_income.reset_index()
    grad_by_income_df.columns = ['Income Category', 'Average Graduation Rate']

    fig1 = px.bar(
        grad_by_income_df,
        x='Income Category',
        y='Average Graduation Rate',
        title='Average 6-Year Graduation Rate by Student Income Level',
        labels={'Average Graduation Rate': 'Graduation Rate (%)'},
        color='Average Graduation Rate',
        color_continuous_scale='RdYlGn',
        text='Average Graduation Rate'
    )

    fig1.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig1.update_layout(
        xaxis_title="Student Income Level (Based on % Receiving Pell Grants)",
        yaxis_title="Average Graduation Rate (%)",
        showlegend=False,
        height=500
    )

    st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # Visualization 2: Scatter plot showing relationship
    st.subheader("🔍 Detailed View: Income vs. Graduation Rate")

    st.markdown("""
    Each point represents a college. The **negative correlation** shows that as the percentage of
    low-income students increases, graduation rates tend to decrease.
    """)

    # Create scatter plot
    fig2 = px.scatter(
        valid_data,
        x=pell_col,
        y=grad_col,
        color='Income_Category',
        title='Relationship Between Student Income and Graduation Rates',
        labels={
            pell_col: '% Students Receiving Pell Grants (Low-Income Indicator)',
            grad_col: '6-Year Graduation Rate (%)'
        },
        opacity=0.6,
        trendline="ols",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig2.update_layout(
        xaxis_title="% Students Receiving Pell Grants (Higher = More Low-Income Students)",
        yaxis_title="Graduation Rate (%)",
        height=600
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Visualization 3: Distribution comparison
    st.subheader("📉 Graduation Rate Distributions by Income Level")

    st.markdown("""
    These distributions show that **low-income serving institutions have a wider range of outcomes**,
    making it even more critical to help students identify the right fit.
    """)

    # Create box plot
    fig3 = px.box(
        valid_data,
        x='Income_Category',
        y=grad_col,
        title='Distribution of Graduation Rates by Student Income Level',
        labels={grad_col: 'Graduation Rate (%)'},
        color='Income_Category',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig3.update_layout(
        xaxis_title="Student Income Level",
        yaxis_title="Graduation Rate (%)",
        showlegend=False,
        height=500
    )

    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Additional context
    st.subheader("💡 What This Means")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### The Problem

        - **Low-income students face barriers** to college completion
        - Schools serving more low-income students often have fewer resources
        - **Graduation rates vary widely**, even among similar institutions
        - Students need guidance to find schools where they'll succeed
        """)

    with col2:
        st.markdown("""
        ### The EquiPath Solution

        - **Personalized recommendations** based on individual student profiles
        - Focus on **equity, affordability, and outcomes**
        - Help students find institutions with **strong support systems**
        - **Data-driven matching** to improve student success rates
        """)

    st.divider()

    # Data notes
    with st.expander("📋 About This Data"):
        st.markdown("""
        ### Data Sources

        - **Pell Grant Recipients**: Percentage of first-time, full-time undergraduates receiving Pell Grants
          - Pell Grants are federal aid for low-income students
          - Higher percentages indicate more low-income students

        - **Graduation Rates**: Bachelor's degree graduation rate within 6 years
          - Standard metric for measuring college completion

        ### Methodology

        Schools are categorized into income levels based on the percentage of students receiving Pell Grants:
        - **Higher Income**: 0-25% Pell recipients
        - **Middle Income**: 25-50% Pell recipients
        - **Lower Income**: 50-75% Pell recipients
        - **Lowest Income**: 75-100% Pell recipients

        Data includes {total_schools:,} institutions with complete income and graduation information.
        """.format(total_schools=len(valid_data)))


if __name__ == "__main__":
    main()
