"""
Script to generate sample Financial data Excel file.
Connected to the VTE Clinical data for POC demonstration.

Financial data includes:
- Department budgets and cost centers
- Per-patient costs (connected via Patient_ID)
- VTE-related treatment costs
- Azure service costs for the analytics platform
"""
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_department_budgets():
    """Generate department budget and cost center data."""
    departments = [
        "Medical ICU", "Surgical ICU", "General Medicine",
        "Orthopedics", "Cardiology", "Oncology", "Neurology", "Emergency"
    ]
    
    # Base budgets and cost per bed-day
    dept_financials = {
        "Medical ICU": {"annual_budget": 8500000, "cost_per_bed_day": 3200, "cost_center": "CC-ICU-001"},
        "Surgical ICU": {"annual_budget": 9200000, "cost_per_bed_day": 3500, "cost_center": "CC-ICU-002"},
        "General Medicine": {"annual_budget": 5500000, "cost_per_bed_day": 1200, "cost_center": "CC-MED-001"},
        "Orthopedics": {"annual_budget": 6800000, "cost_per_bed_day": 2100, "cost_center": "CC-ORT-001"},
        "Cardiology": {"annual_budget": 7200000, "cost_per_bed_day": 2400, "cost_center": "CC-CAR-001"},
        "Oncology": {"annual_budget": 7800000, "cost_per_bed_day": 2800, "cost_center": "CC-ONC-001"},
        "Neurology": {"annual_budget": 6100000, "cost_per_bed_day": 1900, "cost_center": "CC-NEU-001"},
        "Emergency": {"annual_budget": 4200000, "cost_per_bed_day": 950, "cost_center": "CC-EMR-001"},
    }
    
    data = []
    for dept in departments:
        fin = dept_financials[dept]
        data.append({
            "Department": dept,
            "Cost_Center_Code": fin["cost_center"],
            "Annual_Budget_USD": fin["annual_budget"],
            "Cost_Per_Bed_Day_USD": fin["cost_per_bed_day"],
            "VTE_Prevention_Budget_USD": int(fin["annual_budget"] * 0.03),  # 3% for VTE prevention
            "Quality_Incentive_Target_USD": int(fin["annual_budget"] * 0.02),  # 2% quality incentive
            "Fiscal_Year": "FY2024",
        })
    
    return pd.DataFrame(data)


def generate_patient_costs(clinical_df):
    """
    Generate per-patient financial data connected to clinical data.
    Links via Patient_ID from clinical dataset.
    """
    random.seed(42)
    
    # VTE-related cost factors
    vte_treatment_costs = {
        "DVT": {"base": 15000, "variance": 5000},
        "PE": {"base": 35000, "variance": 12000},
        "N/A": {"base": 0, "variance": 0}
    }
    
    prophylaxis_costs = {
        "Enoxaparin": 45,  # per day
        "Heparin": 25,     # per day
        "Mechanical": 15,  # per day (SCD devices)
        "None": 0
    }
    
    dept_base_costs = {
        "Medical ICU": 3200,
        "Surgical ICU": 3500,
        "General Medicine": 1200,
        "Orthopedics": 2100,
        "Cardiology": 2400,
        "Oncology": 2800,
        "Neurology": 1900,
        "Emergency": 950,
    }
    
    data = []
    for _, row in clinical_df.iterrows():
        dept = row["Department"]
        los = row["Length_of_Stay"]
        vte_type = row["VTE_Type"]
        prophylaxis_type = row["Prophylaxis_Type"]
        
        # Calculate base hospitalization cost
        base_cost = dept_base_costs.get(dept, 1500) * los
        
        # Add prophylaxis cost
        prophylaxis_daily_cost = prophylaxis_costs.get(prophylaxis_type, 0)
        prophylaxis_total = prophylaxis_daily_cost * los
        
        # Add VTE treatment cost if event occurred
        vte_cost_info = vte_treatment_costs.get(vte_type, {"base": 0, "variance": 0})
        vte_treatment_cost = 0
        if vte_cost_info["base"] > 0:
            vte_treatment_cost = vte_cost_info["base"] + random.randint(-vte_cost_info["variance"], vte_cost_info["variance"])
        
        # Total cost
        total_cost = base_cost + prophylaxis_total + vte_treatment_cost
        
        # Insurance and patient responsibility
        insurance_coverage = random.uniform(0.70, 0.95)
        insurance_paid = total_cost * insurance_coverage
        patient_responsibility = total_cost - insurance_paid
        
        data.append({
            "Patient_ID": row["Patient_ID"],  # Link to clinical data
            "Admission_Date": row["Admission_Date"],
            "Department": dept,
            "Length_of_Stay_Days": los,
            "Base_Hospitalization_Cost_USD": round(base_cost, 2),
            "Prophylaxis_Cost_USD": round(prophylaxis_total, 2),
            "VTE_Treatment_Cost_USD": round(vte_treatment_cost, 2),
            "Total_Cost_USD": round(total_cost, 2),
            "Insurance_Paid_USD": round(insurance_paid, 2),
            "Patient_Responsibility_USD": round(patient_responsibility, 2),
            "Cost_Category": "VTE Event" if vte_treatment_cost > 0 else "Standard Care",
            "Payer_Type": random.choice(["Medicare", "Medicaid", "Private", "Self-Pay"]),
        })
    
    return pd.DataFrame(data)


def generate_azure_platform_costs():
    """Generate Azure platform costs for the analytics solution."""
    
    # Monthly costs for the demo period (Jan-Jun 2024)
    months = pd.date_range(start="2024-01-01", end="2024-06-30", freq="MS")
    
    data = []
    for month in months:
        # Base costs with some variation
        data.append({
            "Month": month.strftime("%Y-%m"),
            "Azure_OpenAI_Cost_USD": round(random.uniform(8, 15), 2),
            "App_Service_Cost_USD": round(random.uniform(12, 14), 2),
            "Log_Analytics_Cost_USD": round(random.uniform(10, 18), 2),
            "Storage_Cost_USD": round(random.uniform(0.05, 0.15), 2),
            "Functions_Cost_USD": round(random.uniform(0, 0.50), 2),
            "Total_Platform_Cost_USD": 0,  # Will calculate
            "Chat_Requests": random.randint(500, 1500),
            "Tokens_Used": random.randint(800000, 2500000),
        })
    
    # Calculate totals
    df = pd.DataFrame(data)
    df["Total_Platform_Cost_USD"] = (
        df["Azure_OpenAI_Cost_USD"] + 
        df["App_Service_Cost_USD"] + 
        df["Log_Analytics_Cost_USD"] + 
        df["Storage_Cost_USD"] + 
        df["Functions_Cost_USD"]
    ).round(2)
    
    return df


def generate_vte_cost_summary():
    """Generate VTE prevention ROI summary."""
    
    data = [
        {
            "Metric": "VTE Events Prevented (Est.)",
            "Value": 12,
            "Unit": "Events",
            "Cost_Impact_USD": 420000,
            "Notes": "Based on 8% reduction in non-prophylaxis patients"
        },
        {
            "Metric": "Prophylaxis Program Cost",
            "Value": 45000,
            "Unit": "USD",
            "Cost_Impact_USD": -45000,
            "Notes": "Total prophylaxis medication and supplies"
        },
        {
            "Metric": "Net Savings",
            "Value": 375000,
            "Unit": "USD",
            "Cost_Impact_USD": 375000,
            "Notes": "Events prevented - Program cost"
        },
        {
            "Metric": "Quality Incentive Earned",
            "Value": 125000,
            "Unit": "USD",
            "Cost_Impact_USD": 125000,
            "Notes": "Meeting 85% prophylaxis rate target"
        },
        {
            "Metric": "Analytics Platform Cost",
            "Value": 240,
            "Unit": "USD",
            "Cost_Impact_USD": -240,
            "Notes": "6-month Azure platform costs"
        },
        {
            "Metric": "Total ROI",
            "Value": 499760,
            "Unit": "USD",
            "Cost_Impact_USD": 499760,
            "Notes": "Net financial benefit"
        },
    ]
    
    return pd.DataFrame(data)


def main():
    # Load clinical data to create connected financial data
    clinical_path = Path(__file__).parent.parent / "data" / "vte_sample_data.xlsx"
    clinical_df = pd.read_excel(clinical_path, engine='openpyxl')
    
    print(f"Loaded {len(clinical_df)} clinical records")
    
    # Generate financial datasets
    dept_budgets_df = generate_department_budgets()
    patient_costs_df = generate_patient_costs(clinical_df)
    azure_costs_df = generate_azure_platform_costs()
    roi_summary_df = generate_vte_cost_summary()
    
    # Save to Excel with multiple sheets
    output_path = Path(__file__).parent.parent / "data" / "vte_financial_data.xlsx"
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        dept_budgets_df.to_excel(writer, sheet_name='Department_Budgets', index=False)
        patient_costs_df.to_excel(writer, sheet_name='Patient_Costs', index=False)
        azure_costs_df.to_excel(writer, sheet_name='Azure_Platform_Costs', index=False)
        roi_summary_df.to_excel(writer, sheet_name='VTE_ROI_Summary', index=False)
    
    print(f"\nSaved financial data to: {output_path}")
    print(f"\nSheets created:")
    print(f"  1. Department_Budgets: {len(dept_budgets_df)} departments")
    print(f"  2. Patient_Costs: {len(patient_costs_df)} patient records (linked to clinical)")
    print(f"  3. Azure_Platform_Costs: {len(azure_costs_df)} months")
    print(f"  4. VTE_ROI_Summary: {len(roi_summary_df)} metrics")
    
    # Print summary
    print(f"\nFinancial Summary:")
    print(f"  Total Patient Costs: ${patient_costs_df['Total_Cost_USD'].sum():,.2f}")
    print(f"  VTE Treatment Costs: ${patient_costs_df['VTE_Treatment_Cost_USD'].sum():,.2f}")
    print(f"  Total Azure Platform (6mo): ${azure_costs_df['Total_Platform_Cost_USD'].sum():,.2f}")
    print(f"  Estimated ROI: ${roi_summary_df[roi_summary_df['Metric'] == 'Total ROI']['Cost_Impact_USD'].values[0]:,.2f}")


if __name__ == "__main__":
    main()
