"""
Script to generate sample VTE data Excel file.
"""
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_vte_data():
    """Generate sample VTE clinical data."""
    random.seed(42)

    departments = [
        "Medical ICU", "Surgical ICU", "General Medicine",
        "Orthopedics", "Cardiology", "Oncology", "Neurology", "Emergency"
    ]

    physicians = [
        "Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown",
        "Dr. Jones", "Dr. Garcia", "Dr. Miller", "Dr. Davis",
        "Dr. Rodriguez", "Dr. Martinez"
    ]

    data = []
    base_date = datetime(2024, 1, 1)

    # Department-specific base rates to create realistic variation
    dept_base_rate = {
        "Medical ICU": 0.92,
        "Surgical ICU": 0.88,
        "General Medicine": 0.78,
        "Orthopedics": 0.95,
        "Cardiology": 0.85,
        "Oncology": 0.82,
        "Neurology": 0.80,
        "Emergency": 0.72
    }

    for i in range(150):
        dept = random.choice(departments)

        # Determine if prophylaxis was given based on department rate
        prophylaxis_given = random.random() < dept_base_rate.get(dept, 0.80)

        # VTE events are more likely without prophylaxis
        vte_event = random.random() < (0.02 if prophylaxis_given else 0.08)

        # Random admission date within 6 months
        admission_date = base_date + timedelta(days=random.randint(0, 180))

        # Risk score influences prophylaxis adherence slightly
        risk_score = random.choices(
            ["Low", "Moderate", "High"],
            weights=[0.3, 0.45, 0.25]
        )[0]

        data.append({
            "Patient_ID": f"PT{1000 + i}",
            "Admission_Date": admission_date,
            "Discharge_Date": admission_date + timedelta(days=random.randint(1, 14)),
            "Department": dept,
            "Attending_Physician": random.choice(physicians),
            "VTE_Risk_Score": risk_score,
            "Prophylaxis_Ordered": "Yes" if prophylaxis_given else "No",
            "Prophylaxis_Given": "Yes" if prophylaxis_given else "No",
            "Prophylaxis_Type": random.choice(["Enoxaparin", "Heparin", "Mechanical"]) if prophylaxis_given else "None",
            "VTE_Event": "Yes" if vte_event else "No",
            "VTE_Type": random.choice(["DVT", "PE"]) if vte_event else "N/A",
            "Length_of_Stay": random.randint(1, 14),
            "Age": random.randint(25, 85),
            "Gender": random.choice(["Male", "Female"]),
            "BMI": round(random.uniform(18.5, 40.0), 1),
            "Mobility_Status": random.choice(["Ambulatory", "Limited", "Bedbound"]),
        })

    return pd.DataFrame(data)


def main():
    # Generate data
    df = generate_vte_data()

    # Save to Excel
    output_path = Path(__file__).parent.parent / "data" / "vte_sample_data.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(output_path, index=False, sheet_name="VTE_Data")

    print(f"Generated {len(df)} records")
    print(f"Saved to: {output_path}")

    # Print summary statistics
    print("\nSummary:")
    print(f"  Overall Prophylaxis Rate: {(df['Prophylaxis_Given'] == 'Yes').mean() * 100:.1f}%")
    print(f"  VTE Event Rate: {(df['VTE_Event'] == 'Yes').mean() * 100:.1f}%")
    print(f"  Date Range: {df['Admission_Date'].min().strftime('%Y-%m-%d')} to {df['Admission_Date'].max().strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
