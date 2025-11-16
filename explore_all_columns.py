"""
Comprehensive column exploration for enhanced feature engineering.
Maps all available columns to potential use in indices.
"""

import pandas as pd
import os

# Load datasets
print("Loading datasets...")
college_results = pd.read_excel(os.path.join("data", "College Results View 2021 Data Dump for Export.xlsx"))
affordability_gap = pd.read_excel(os.path.join("data", "Affordability Gap Data AY2022-23 2.17.25.xlsx"))

print(f"\nCollege Results: {len(college_results)} rows, {len(college_results.columns)} columns")
print(f"Affordability Gap: {len(affordability_gap)} rows, {len(affordability_gap.columns)} columns")

print("\n" + "="*100)
print("COLUMN EXPLORATION FOR ENHANCED INDICES")
print("="*100)

# Support Infrastructure Index columns
print("\n📚 SUPPORT INFRASTRUCTURE INDEX")
print("-" * 100)
support_keywords = ['FACULTY', 'ENDOWMENT', 'PELL', 'TRANSFER', 'STUDENT', 'RATIO', 'RESOURCE', 'EXPENDITURE']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in support_keywords):
        print(f"   {col}")

# Environment & Personalization columns
print("\n🏫 ENVIRONMENT & PERSONALIZATION INDEX")
print("-" * 100)
env_keywords = ['SIZE', 'URBAN', 'RURAL', 'CARNEGIE', 'LOCATION', 'REGION', 'DEGREE OF', 'AGE']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in env_keywords):
        print(f"   {col}")

# Academic Offerings columns
print("\n📖 ACADEMIC OFFERINGS INDEX")
print("-" * 100)
academic_keywords = ['DEGREE', 'BACHELOR', 'MASTER', 'DOCTORAL', 'ASSOCIATE', 'PROGRAM', 'MAJOR', 'FIELD']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in academic_keywords):
        # Only show summary columns, not individual fields
        if 'TOTAL' in col.upper() or 'GRAND' in col.upper() or 'LEVEL' in col.upper() or 'HIGHEST' in col.upper():
            print(f"   {col}")

# ROI enhancement columns
print("\n💰 ROI INDEX (Enhanced)")
print("-" * 100)
roi_keywords = ['EARN', 'DEBT', 'DEFAULT', 'REPAY', 'SALARY', 'INCOME']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in roi_keywords):
        print(f"   {col}")

# Equity enhancement columns
print("\n⚖️ EQUITY INDEX (Enhanced)")
print("-" * 100)
equity_keywords = ['GRAD', 'COMPLET', 'RETENTION', 'RACE', 'ETHNIC', 'MSI', 'HBCU', 'HSI', 'TRIBAL']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in equity_keywords):
        if 'RATE' in col.upper() or 'PERCENT' in col.upper() or col.upper() in ['MSI STATUS', 'HBCU', 'HSI', 'TRIBAL', 'PBI']:
            print(f"   {col}")

# Affordability enhancement columns
print("\n💵 AFFORDABILITY INDEX (Enhanced)")
print("-" * 100)
for col in affordability_gap.columns:
    if any(kw in col.upper() for kw in ['GAP', 'PRICE', 'COST', 'WAGE', 'INCOME', 'CHILD CARE', 'TTD', 'WORK STUDY']):
        print(f"   {col}")

# Access/Selectivity columns
print("\n🚪 ACCESS INDEX (Enhanced)")
print("-" * 100)
access_keywords = ['ADMIT', 'ACCEPT', 'SAT', 'ACT', 'TEST', 'OPEN', 'SELECTIVE']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in access_keywords):
        if 'RATE' in col.upper() or 'PERCENT' in col.upper() or 'POLICY' in col.upper() or 'SCORE' in col.upper():
            print(f"   {col}")

# Demographics & student body
print("\n👥 STUDENT BODY DEMOGRAPHICS")
print("-" * 100)
demo_keywords = ['INTERNATIONAL', 'GENDER', 'WOMEN', 'MEN', 'AGE 25', 'NONTRADITIONAL']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in demo_keywords):
        if 'PERCENT' in col.upper() or 'NUMBER' in col.upper():
            print(f"   {col}")

# Institution characteristics
print("\n🏛️ INSTITUTION CHARACTERISTICS")
print("-" * 100)
char_keywords = ['SECTOR', 'CONTROL', 'INSTITUTIONAL CATEGORY', 'INSTITUTION LEVEL']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in char_keywords):
        print(f"   {col}")

# Location data
print("\n📍 LOCATION DATA")
print("-" * 100)
loc_keywords = ['STATE', 'CITY', 'REGION', 'LATITUDE', 'LONGITUDE', 'ZIP', 'COUNTY']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in loc_keywords):
        print(f"   {col}")

print("\n" + "="*100)
print("EXPLORATION COMPLETE")
print("="*100)
