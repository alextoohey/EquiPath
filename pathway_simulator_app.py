import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="College Pathway Simulator",
    page_icon="🎓",
    layout="wide"
)

# Title and description
st.title("🎓 College Pathway Simulator")
st.markdown("""
**Find the best educational path based on your situation.**  
Compare costs, debt, and earnings across different college pathways.
""")

# Load data (cached for performance)
@st.cache_data
def load_data():
    dfa = pd.read_csv("/Users/leozhang/7thDatathon/Affordability Gap Data AY2022-23 2.17.25.xlsx - Affordability_latest_02-17-25 1.csv")
    dfc = pd.read_csv("/Users/leozhang/7thDatathon/College Results View 2021 Data Dump for Export.xlsx - College Results View 2021 Data .csv")
    return dfa, dfc

try:
    dfa, dfc = load_data()
    
    # Sidebar for user inputs
    st.sidebar.header("📋 Your Information")
    
    # Get unique states
    states = sorted(dfa['State Abbreviation'].dropna().unique())
    
    # User inputs
    selected_state = st.sidebar.selectbox(
        "Select Your State",
        options=['National Average'] + list(states),
        index=0
    )
    
    income_options = {
        '$0 - $30,000 (Low Income)': 30000,
        '$30,001 - $48,000': 48000,
        '$48,001 - $75,000': 75000,
        '$75,001 - $110,000': 110000,
        '$110,001 - $150,000': 150000
    }
    
    selected_income_label = st.sidebar.selectbox(
        "Family Income Bracket",
        options=list(income_options.keys()),
        index=0
    )
    income_bracket = income_options[selected_income_label]
    
    # Add "Calculate" button
    if st.sidebar.button("🔍 Find My Best Path", type="primary"):
        
        # Filter data
        dfa_filtered = dfa[dfa['Student Family Earnings Ceiling'] == income_bracket].copy()
        
        # Merge datasets
        df_merged = dfa_filtered.merge(
            dfc,
            left_on='Unit ID',
            right_on='UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION',
            how='inner'
        )
        
        # Apply state filter
        if selected_state != 'National Average':
            df_merged = df_merged[df_merged['State Abbreviation'] == selected_state]
        
        # Check if we have data
        if len(df_merged) == 0:
            st.error(f"❌ No data available for {selected_state} in this income bracket.")
        else:
            # Create pathway categories
            cc = df_merged[df_merged['Sector Name'] == 'Public, 2-year'].copy()
            pub = df_merged[df_merged['Sector Name'] == 'Public, 4-year or above'].copy()
            priv = df_merged[df_merged['Sector Name'] == 'Private not-for-profit, 4-year or above'].copy()
            
            # Display institution counts
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Community Colleges", len(cc))
            with col2:
                st.metric("Public Universities", len(pub))
            with col3:
                st.metric("Private Universities", len(priv))
            
            if len(cc) == 0 or len(pub) == 0:
                st.warning("⚠️ Not enough institutions for comparison. Try 'National Average'.")
            else:
                # Calculate pathway statistics
                # For Path A, prioritize high-transfer community colleges
                HIGH_TRANSFER_THRESHOLD = 9  # Use median or above
                
                cc_high_transfer = cc[
                    (cc['Transfer Out Rate'].notna()) & 
                    (cc['Transfer Out Rate'] >= HIGH_TRANSFER_THRESHOLD)
                ].copy()
                
                # Use high-transfer CCs if available, otherwise all CCs
                if len(cc_high_transfer) >= 5:
                    cc_for_path_a = cc_high_transfer
                    using_transfer_filter = True
                else:
                    cc_for_path_a = cc
                    using_transfer_filter = False
                
                cc_price = cc_for_path_a['Net Price'].median()
                cc_debt = cc['Median Debt of Completers'].median()
                cc_earnings = cc['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'].median()
                
                pub_price = pub['Net Price'].median()
                pub_debt = pub['Median Debt of Completers'].median()
                pub_earnings = pub['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'].median()
                
                priv_price = priv['Net Price'].median() if len(priv) > 0 else 0
                priv_debt = priv['Median Debt of Completers'].median() if len(priv) > 0 else 0
                priv_earnings = priv['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'].median() if len(priv) > 0 else 0
                
                # Calculate pathways
                path_a_cost = (cc_price * 2) + (pub_price * 2)
                path_a_investment = path_a_cost + pub_debt
                path_a_value = (pub_earnings * 10) - path_a_investment
                
                path_b_cost = pub_price * 4
                path_b_investment = path_b_cost + pub_debt
                path_b_value = (pub_earnings * 10) - path_b_investment
                
                path_c_cost = priv_price * 4
                path_c_investment = path_c_cost + priv_debt
                path_c_value = (priv_earnings * 10) - path_c_investment
                
                # Display pathways
                st.header("🛤️ Your Pathway Options")
                
                st.info("""
                📊 **About This Data:** 
                - **Net prices** are specific to your income bracket and include financial aid
                - **Earnings** represent graduates 10 years after enrollment (aggregated at state/regional level)
                - **Path A earnings** use public university data since transfer students graduate with the same degree
                - All dollar amounts are medians (middle values), so half of students experience better outcomes
                """)
                
                tab1, tab2, tab3 = st.tabs(["Path A: CC → Public", "Path B: Direct Public", "Path C: Direct Private"])
                
                with tab1:
                    st.subheader("🎓 Community College (2yr) → Public University (2yr)")
                    
                    if using_transfer_filter:
                        st.success(f"""
                        ✅ **Using High-Transfer Community Colleges**
                        - {len(cc_for_path_a)} colleges with ≥{HIGH_TRANSFER_THRESHOLD}% transfer rate
                        - Average transfer rate: {cc_for_path_a['Transfer Out Rate'].mean():.1f}%
                        - These CCs have strong track records of preparing students for 4-year universities
                        """)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total 4-Year Cost", f"${path_a_cost:,.0f}")
                    with col2:
                        st.metric("Expected Debt", f"${pub_debt:,.0f}")
                    with col3:
                        st.metric("Annual Earnings (10yr)", f"${pub_earnings:,.0f}")
                    with col4:
                        st.metric("Net 10-Year Value", f"${path_a_value:,.0f}")
                    
                    st.info(f"⏱️ **Break Even Time:** {path_a_investment/pub_earnings:.1f} years")
                
                with tab2:
                    st.subheader("🎓 Public University (4 years)")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total 4-Year Cost", f"${path_b_cost:,.0f}")
                    with col2:
                        st.metric("Expected Debt", f"${pub_debt:,.0f}")
                    with col3:
                        st.metric("Annual Earnings (10yr)", f"${pub_earnings:,.0f}")
                    with col4:
                        st.metric("Net 10-Year Value", f"${path_b_value:,.0f}")
                    
                    st.info(f"⏱️ **Break Even Time:** {path_b_investment/pub_earnings:.1f} years")
                
                with tab3:
                    if len(priv) > 0:
                        st.subheader("🎓 Private University (4 years)")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total 4-Year Cost", f"${path_c_cost:,.0f}")
                        with col2:
                            st.metric("Expected Debt", f"${priv_debt:,.0f}")
                        with col3:
                            st.metric("Annual Earnings (10yr)", f"${priv_earnings:,.0f}")
                        with col4:
                            st.metric("Net 10-Year Value", f"${path_c_value:,.0f}")
                        
                        st.info(f"⏱️ **Break Even Time:** {path_c_investment/priv_earnings:.1f} years")
                    else:
                        st.warning("No private universities available in this area.")
                
                # Comparison chart
                st.header("📊 Side-by-Side Comparison")
                
                # Create comparison data
                comparison_data = {
                    'Pathway': ['A: CC→Public', 'B: Direct Public', 'C: Direct Private'],
                    'Total Cost': [path_a_cost, path_b_cost, path_c_cost],
                    'Expected Debt': [pub_debt, pub_debt, priv_debt],
                    'Total Investment': [path_a_investment, path_b_investment, path_c_investment],
                    '10-Year Net Value': [path_a_value, path_b_value, path_c_value]
                }
                
                comparison_df = pd.DataFrame(comparison_data)
                
                # Display as table
                st.dataframe(
                    comparison_df.style.format({
                        'Total Cost': '${:,.0f}',
                        'Expected Debt': '${:,.0f}',
                        'Total Investment': '${:,.0f}',
                        '10-Year Net Value': '${:,.0f}'
                    }),
                    use_container_width=True
                )
                
                # Bar chart comparison
                fig = go.Figure(data=[
                    go.Bar(name='Total 4-Year Cost', x=comparison_df['Pathway'], y=comparison_df['Total Cost']),
                    go.Bar(name='Expected Debt', x=comparison_df['Pathway'], y=comparison_df['Expected Debt'])
                ])
                
                fig.update_layout(
                    title='Cost and Debt Comparison',
                    barmode='group',
                    yaxis_title='Amount ($)',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Recommendation
                st.header("💡 Our Recommendation")
                
                best_path = comparison_df.loc[comparison_df['10-Year Net Value'].idxmax()]
                savings = path_b_cost - path_a_cost
                
                st.success(f"""
                **✅ We recommend: {best_path['Pathway']}**
                
                - Best 10-year net value: **${best_path['10-Year Net Value']:,.0f}**
                - Path A saves you **${savings:,.0f}** compared to going straight to a 4-year university
                - You'll break even in just **{path_a_investment/pub_earnings:.1f} years**!
                """)
                
                # Top schools
                st.header("🏫 Top Affordable Schools")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Community Colleges")
                    top_cc = cc.nsmallest(5, 'Net Price')[['Institution Name_x', 'City', 'Net Price']]
                    top_cc.columns = ['Institution', 'City', 'Net Price/Year']
                    st.dataframe(
                        top_cc.style.format({'Net Price/Year': '${:,.0f}'}),
                        hide_index=True,
                        use_container_width=True
                    )
                
                with col2:
                    st.subheader("Public Universities")
                    top_pub = pub.nsmallest(5, 'Net Price')[['Institution Name_x', 'City', 'Net Price']]
                    top_pub.columns = ['Institution', 'City', 'Net Price/Year']
                    st.dataframe(
                        top_pub.style.format({'Net Price/Year': '${:,.0f}'}),
                        hide_index=True,
                        use_container_width=True
                    )
                
                # Best Community Colleges for Transfer
                if len(cc) > 0 and cc['Transfer Out Rate'].notna().sum() > 0:
                    st.header("🔄 Best Community Colleges for Transferring")
                    st.markdown("""
                    These community colleges have the **highest transfer-out rates**, meaning more students 
                    successfully transfer to 4-year universities. Perfect for Path A!
                    """)
                    
                    # Filter to CCs with transfer data
                    cc_with_transfer = cc[cc['Transfer Out Rate'].notna()].copy()
                    
                    # Get top transfer CCs (at least 10% or top 10, whichever gives more schools)
                    top_transfer = cc_with_transfer.nlargest(min(10, len(cc_with_transfer)), 'Transfer Out Rate')[[
                        'Institution Name_x',
                        'City',
                        'Transfer Out Rate',
                        'Net Price',
                    ]].copy()
                    
                    # Add retention rate if available
                    if 'First-Time, Full-Time Retention Rate' in cc_with_transfer.columns:
                        top_transfer_full = cc_with_transfer.nlargest(min(10, len(cc_with_transfer)), 'Transfer Out Rate')[[
                            'Institution Name_x',
                            'City',
                            'Transfer Out Rate',
                            'Net Price',
                            'First-Time, Full-Time Retention Rate'
                        ]].copy()
                        top_transfer_full.columns = [
                            'Institution',
                            'City',
                            'Transfer Rate',
                            'Net Price/Year',
                            'Retention Rate'
                        ]
                        st.dataframe(
                            top_transfer_full.style.format({
                                'Transfer Rate': '{:.0f}%',
                                'Net Price/Year': '${:,.0f}',
                                'Retention Rate': '{:.1f}%'
                            }),
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        top_transfer.columns = [
                            'Institution',
                            'City',
                            'Transfer Rate',
                            'Net Price/Year',
                        ]
                        st.dataframe(
                            top_transfer.style.format({
                                'Transfer Rate': '{:.0f}%',
                                'Net Price/Year': '${:,.0f}',
                            }),
                            hide_index=True,
                            use_container_width=True
                        )
                    
                    # Show stats
                    avg_transfer = cc_with_transfer['Transfer Out Rate'].mean()
                    median_transfer = cc_with_transfer['Transfer Out Rate'].median()
                    st.caption(f"📊 Average transfer rate: {avg_transfer:.1f}% | Median: {median_transfer:.0f}%")
                    st.caption(f"💡 Higher transfer rates indicate better preparation for 4-year universities")
                
                # Best Value Schools - Hidden Gems
                st.header("💎 Hidden Gems - Best Value Schools")
                st.markdown("""
                These schools offer exceptional value **regardless of type**. They combine low net price with high graduate earnings.
                """)
                
                # Calculate ROI score for all schools in the filtered dataset
                df_with_roi = df_merged.copy()
                
                # Only calculate for schools with complete data
                df_with_roi = df_with_roi[
                    df_with_roi['Net Price'].notna() & 
                    df_with_roi['Median Debt of Completers'].notna() &
                    df_with_roi['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'].notna()
                ].copy()
                
                # Calculate total investment and ROI score
                df_with_roi['Total Investment'] = (
                    df_with_roi['Net Price'] * 4 + 
                    df_with_roi['Median Debt of Completers']
                )
                
                df_with_roi['ROI Score'] = (
                    df_with_roi['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'] * 10 - 
                    df_with_roi['Total Investment']
                ) / df_with_roi['Total Investment']
                
                # Get top 10 best value schools
                best_value = df_with_roi.nlargest(10, 'ROI Score')[[
                    'Institution Name_x',
                    'City', 
                    'Sector Name',
                    'Net Price',
                    'Median Debt of Completers',
                    'Median Earnings of Students Working and Not Enrolled 10 Years After Entry',
                    'ROI Score'
                ]].copy()
                
                best_value.columns = [
                    'Institution', 
                    'City',
                    'Type',
                    'Net Price/Year',
                    'Expected Debt',
                    '10-Year Earnings',
                    'ROI Score'
                ]
                
                st.dataframe(
                    best_value.style.format({
                        'Net Price/Year': '${:,.0f}',
                        'Expected Debt': '${:,.0f}',
                        '10-Year Earnings': '${:,.0f}',
                        'ROI Score': '{:.2f}x'
                    }),
                    hide_index=True,
                    use_container_width=True
                )
                
                st.caption("💡 ROI Score = (10-Year Earnings - Total Investment) / Total Investment. Higher is better!")
                
                # Most Affordable Options (regardless of type)
                st.header("💰 Most Affordable Options")
                st.markdown("""
                All schools available in your area, sorted by net price. Sometimes a private school with excellent aid 
                can be cheaper than public options!
                """)
                
                # Get all schools sorted by net price
                affordable_all = df_merged[
                    df_merged['Net Price'].notna()
                ].nsmallest(15, 'Net Price')[[
                    'Institution Name_x',
                    'City',
                    'Sector Name',
                    'Net Price',
                    'Median Earnings of Students Working and Not Enrolled 10 Years After Entry'
                ]].copy()
                
                affordable_all.columns = [
                    'Institution',
                    'City', 
                    'Type',
                    'Net Price/Year',
                    '10-Year Earnings'
                ]
                
                st.dataframe(
                    affordable_all.style.format({
                        'Net Price/Year': '${:,.0f}',
                        '10-Year Earnings': '${:,.0f}'
                    }),
                    hide_index=True,
                    use_container_width=True
                )
    
    else:
        # Show instructions before calculation
        st.info("👈 Select your state and income bracket in the sidebar, then click 'Find My Best Path' to see your options!")
        
        # Show some stats about the tool
        st.header("📈 About This Tool")
        st.markdown("""
        This tool helps you understand the **true cost** of different college pathways by showing:
        
        - 💵 **Total 4-year costs** (what you'll actually pay after financial aid)
        - 💳 **Expected debt** (median debt for graduates)
        - 💰 **10-year earnings** (median salary 10 years after graduation)
        - 🎯 **Net value** (total earnings minus total investment)
        
        **Why it matters:** Many students assume expensive private schools lead to better outcomes. 
        The data often shows that starting at community college and transferring to a public university 
        provides the **best value** - saving money while achieving similar earnings.
        """)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Make sure the CSV files are in the same directory as this script.")