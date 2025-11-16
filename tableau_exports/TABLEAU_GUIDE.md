# Tableau Visualization Guide for EquiPath Data Insights

This guide shows you how to recreate the exact visualizations from the Data Insights Streamlit page in Tableau.

## Files Provided

1. **income_graduation_data.csv** - Individual school data (1,821 schools)
   - Institution Name
   - State of Institution
   - Pell_Grant_Percent (% low-income students)
   - Graduation_Rate_6yr
   - Income_Category (text labels)
   - Income_Category_Num (for sorting)

2. **income_categories_summary.csv** - Aggregated data by income category
   - Income_Category
   - Average_Graduation_Rate
   - Number_of_Schools

3. **key_statistics.csv** - Key metrics for KPIs
   - Metric names
   - Values
   - Formatted labels

---

## Visualization 1: Bar Chart - Graduation Rates by Income Level

### Data Source
Use: `income_categories_summary.csv`

### Steps in Tableau

1. **Connect to Data**
   - Open Tableau
   - Connect to Text File → Select `income_categories_summary.csv`

2. **Create the Bar Chart**
   - Drag `Income_Category` to Columns
   - Drag `Average_Graduation_Rate` to Rows
   - Right-click `Income_Category` → Sort → Sort By: `Income_Category_Num`, Ascending

3. **Add Color**
   - Drag `Average_Graduation_Rate` to Color
   - Click Color → Edit Colors
   - Choose Color Palette: "Red-Yellow-Green Diverging" or "Traffic Light"
   - Click Reversed if needed (green should be high values)

4. **Add Data Labels**
   - Drag `Average_Graduation_Rate` to Label
   - Right-click Label → Format → Number Format → Percentage (1 decimal place)
   - Or use Custom format: `0.0"%"`

5. **Format the Chart**
   - Right-click axis → Edit Axis
   - Axis Title: "Average Graduation Rate (%)"
   - Title: "Average 6-Year Graduation Rate by Student Income Level"

6. **Polish**
   - Format → Borders → None
   - Format → Gridlines → Remove vertical gridlines

---

## Visualization 2: Scatter Plot - Income vs. Graduation Rate

### Data Source
Use: `income_graduation_data.csv`

### Steps in Tableau

1. **Connect to Data**
   - Connect to Text File → Select `income_graduation_data.csv`

2. **Create the Scatter Plot**
   - Drag `Pell_Grant_Percent` to Columns
   - Drag `Graduation_Rate_6yr` to Rows

3. **Add Color by Category**
   - Drag `Income_Category` to Color
   - Click Color → Edit Colors → Choose a 4-color palette
   - Recommended: "Tableau 10" or "Color Blind"

4. **Adjust Mark Size & Transparency**
   - Click on Marks card → Change to "Circle"
   - Click Size → Adjust to medium
   - Click Color → Transparency → Set to 60-70%

5. **Add Trendline**
   - Click Analytics pane (top menu)
   - Drag "Trend Line" onto the chart
   - Select "Linear"
   - Right-click trendline → Edit → Show confidence bands (optional)

6. **Format Axes**
   - Right-click X-axis → Edit Axis
     - Title: "% Students Receiving Pell Grants (Higher = More Low-Income Students)"
   - Right-click Y-axis → Edit Axis
     - Title: "6-Year Graduation Rate (%)"
   - Title: "Relationship Between Student Income and Graduation Rates"

7. **Add Tooltips**
   - Click Tooltip on Marks card
   - Add: `Institution Name`, `State of Institution`, `Pell_Grant_Percent`, `Graduation_Rate_6yr`

---

## Visualization 3: Box Plot - Distribution by Income Level

### Data Source
Use: `income_graduation_data.csv`

### Steps in Tableau

1. **Create the Box Plot**
   - Drag `Income_Category` to Columns
   - Drag `Graduation_Rate_6yr` to Rows
   - Right-click `Income_Category` → Sort → Sort By: `Income_Category_Num`, Ascending

2. **Change to Box Plot**
   - Click Analytics pane
   - Drag "Box Plot" onto the view
   - Or: Show Me menu → Select Box-and-Whisker plot

3. **Alternative: Manual Box Plot**
   - Right-click `Graduation_Rate_6yr` (on Rows) → Add Reference Line
   - Select "Box Plot" from the options
   - Configure: Show median, quartiles, whiskers

4. **Add Color by Category**
   - Drag `Income_Category` to Color
   - Use the same color scheme as the scatter plot for consistency

5. **Format**
   - Title: "Distribution of Graduation Rates by Student Income Level"
   - X-axis: "Student Income Level"
   - Y-axis: "Graduation Rate (%)"

---

## Dashboard: Combine All Visualizations

### Create a Dashboard

1. **New Dashboard**
   - Click Dashboard → New Dashboard
   - Set size: Automatic or 1200 x 800

2. **Add Sheets**
   - Drag the three worksheets (Bar Chart, Scatter Plot, Box Plot) onto the dashboard
   - Arrange vertically or in a grid

3. **Add KPIs (Key Statistics)**
   - Create a new worksheet
   - Connect to `key_statistics.csv`
   - Drag `Metric` to Rows
   - Drag `Label` to Text
   - Format as a table or use BANs (Big Ass Numbers)
   - Add this to the top of your dashboard

4. **Add Title & Description**
   - Dashboard → Objects → Text
   - Add title: "📊 Data Insights: Income & Educational Equity"
   - Add description explaining the problem

5. **Add Filters (Optional)**
   - Drag `State of Institution` to Filters (from income_graduation_data)
   - Show filter → Dropdown or Multiple Values List
   - Apply to all worksheets using this data source

6. **Format Dashboard**
   - Dashboard → Format → Shading
   - Add padding/spacing between visualizations
   - Use consistent color scheme throughout

---

## Color Recommendations

To match the Plotly theme:

### Bar Chart
- Use a gradient from red (low) to green (high)
- Tableau Palette: "Red-Gold-Green Diverging"

### Scatter Plot
- Higher Income: Blue (#3366CC)
- Middle Income: Green (#669966)
- Lower Income: Orange (#FF9933)
- Lowest Income: Red (#CC3333)

### Box Plot
- Use the same colors as scatter plot

---

## Tips for Presentation

1. **Keep it Simple**
   - Don't add too many filters or interactions
   - Focus on the key message: income gap in graduation rates

2. **Use Annotations**
   - Right-click a data point → Annotate → Point
   - Highlight the gap between highest and lowest income groups

3. **Export Options**
   - Dashboard → Export as Image (for presentations)
   - Dashboard → Export as PDF
   - Worksheet → Save as Workbook to Tableau Public (for sharing)

4. **Interactive Features**
   - Add dashboard actions: hover to highlight
   - Add URL actions to link to EquiPath Streamlit app

---

## Quick Start

1. Open Tableau Desktop
2. Connect to `income_categories_summary.csv`
3. Create bar chart (5 minutes)
4. Connect to `income_graduation_data.csv` (add as new data source)
5. Create scatter plot (5 minutes)
6. Create box plot (5 minutes)
7. Build dashboard (5 minutes)

**Total time: ~20-30 minutes**

---

## Troubleshooting

**Issue: Categories in wrong order**
- Solution: Sort by `Income_Category_Num` field

**Issue: Colors don't match**
- Solution: Edit Colors → Select specific palette → Assign manually

**Issue: Trendline not showing**
- Solution: Make sure both axes are continuous (green pills, not blue)

**Issue: Box plot not appearing**
- Solution: Ensure `Graduation_Rate_6yr` is aggregated (SUM, AVG, etc.)

---

## Need Help?

Reference the Streamlit page at `pages/4_📊_Data_Insights.py` to see the exact visualizations you're recreating.

The data is clean and ready to use - just import and visualize!
