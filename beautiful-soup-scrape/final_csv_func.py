import os
import pandas as pd
import re

def extract_year(season_str):
    """Extracts the year from the 'Season' column, e.g. 'Fall 2021' -> 2021"""
    match = re.search(r'(\d{4})', str(season_str))
    return int(match.group(1)) if match else None

def combine_and_sort_by_year(folder_path, output_file):
    combined_df = pd.DataFrame()

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)

            # Drop 'Look Number' if present
            if 'Look Number' in df.columns:
                df = df.drop(columns=['Look Number'])

            combined_df = pd.concat([combined_df, df], ignore_index=True)

    if combined_df.empty:
        print("⚠️ No CSV data found.")
        return

    # Extract year and sort only by year
    combined_df['Year'] = combined_df['Season'].apply(extract_year)
    combined_df.sort_values(by='Year', inplace=True)
    combined_df.drop(columns=['Year'], inplace=True)

    # Save the final combined CSV
    combined_df.to_csv(output_file, index=False)
    print(f"✅ Combined CSV saved as: {output_file}")

# 🔧 Run the function
combine_and_sort_by_year(folder_path='final_brand_csvs', output_file='combined_sorted_fashion.csv')
