import csv
import os
import re
from collections import defaultdict
from typing import Dict, List, Set, Optional

# --- Plotting/Data Handling Imports ---
import pandas as pd
import matplotlib.pyplot as plt
from pandas.api.types import CategoricalDtype # For ordering season terms

# --- Helper Function: Standardize Season (MODIFIED for distinct seasons) ---
def standardize_season(season_str: str) -> str:
    """
    Standardizes season strings into distinct terms (spring, summer, fall, winter, etc.)
    while preserving the associated 4-digit year if found.
    """
    # Basic input validation
    if not isinstance(season_str, str) or not season_str:
        return "unknown_format" # Return a specific string for invalid input

    original_cleaned = season_str.strip()
    year: Optional[str] = None
    standardized_term: str = "unknown_term" # Default term if logic fails

    # Try to extract a 4-digit year using regex (\b ensures whole word)
    year_match = re.search(r'\b(\d{4})\b', original_cleaned)

    if year_match:
        year = year_match.group(1)
        # Remove the year and potential surrounding whitespace/separators to isolate the term
        term_part = re.sub(r'\b' + re.escape(year) + r'\b', '', original_cleaned).strip()
        # Clean up common separators potentially left over (e.g., "Fall / ", "/ Winter")
        term_part = re.sub(r'^[/\s-]+|[/\s-]+$', '', term_part).strip()
    else:
        # No 4-digit year found, treat the whole string as the term part
        term_part = original_cleaned

    # If only a year was present, or term became empty after removing year
    if not term_part:
         standardized_term = "year_only" # Or some other indicator
    else:
        # Standardize the term part (case-insensitive)
        term_lower = term_part.lower()

        # --- Apply NEW standardization rules for distinct seasons ---
        # Specific terms first, order can matter if keywords overlap
        if "pre-fall" in term_lower:
            standardized_term = "pre-fall"
        elif "resort" in term_lower or "cruise" in term_lower:
            standardized_term = "resort"
        elif "couture" in term_lower: # Example specific category
            standardized_term = "couture"
        # Handle primary seasons distinctly
        elif "spring" in term_lower:
             standardized_term = "spring"
        elif "summer" in term_lower:
             standardized_term = "summer"
        elif "ss" in term_lower: # Map 'ss' -> 'spring'
             standardized_term = "spring"
        elif "fall" in term_lower:
             standardized_term = "fall"
        elif "autumn" in term_lower: # Map 'autumn' -> 'fall'
             standardized_term = "fall"
        elif "winter" in term_lower:
             standardized_term = "winter"
        elif "aw" in term_lower: # Map 'aw' -> 'fall'
             standardized_term = "fall"
        else:
            standardized_term = term_lower

    # --- Combine standardized term and year ---
    if year:
        if standardized_term == "year_only":
             return f"unknown_term {year}"
        return f"{standardized_term} {year}"
    else:
        return standardized_term


# --- CSV Reading Function ---
def csv_to_dict(file_path: str, encoding: str = 'utf-8', delimiter: str = ',') -> Dict[str, List[str]]:
    """
    Reads CSV to a dict of lists (headers->keys, columns->values).
    Handles file not found and basic read errors, returning {}.
    Returns empty dict {} if file is empty or headerless.
    """
    data_dict: Dict[str, List[str]] = {}
    try:
        with open(file_path, mode='r', newline='', encoding=encoding) as infile:
            reader = csv.DictReader(infile, delimiter=delimiter)

            if not reader.fieldnames:
                return {}

            headers = reader.fieldnames
            data_dict = {header: [] for header in headers}

            for row in reader:
                for header in headers:
                    data_dict[header].append(row.get(header, ''))
        return data_dict
    except FileNotFoundError:
         return {}
    except Exception as e:
         print(f"Warning: Error reading CSV '{os.path.basename(file_path)}': {e}. Skipping file.")
         return {}


# --- Configuration: Set your CSV directory path here ---
CSV_FOLDER_PATH = os.path.join(os.getcwd(), "beautiful-soup-scrape", "final_brand_csvs")


# --- Main Script Logic ---

# 1. Read and Process CSV Files
csv_list = []
print(f"Looking for CSV files in: {CSV_FOLDER_PATH}")

if not os.path.isdir(CSV_FOLDER_PATH):
    print(f"Error: Directory not found at '{CSV_FOLDER_PATH}'")
    exit()

print("Starting CSV processing...")
for filename in os.listdir(CSV_FOLDER_PATH):
    file_path = os.path.join(CSV_FOLDER_PATH, filename)
    if filename.lower().endswith(".csv") and os.path.isfile(file_path):
        sheet_data = csv_to_dict(file_path)
        if sheet_data:
            csv_list.append(sheet_data)

print(f"\nSuccessfully loaded data from {len(csv_list)} CSV files.")

# 2. Aggregate Data by Standardized Season/Year (MODIFIED TO COUNT DESIGNS)
# Structure: Dict[season_year_key, Dict[designer, design_count]]
# Use nested defaultdicts for easy counting
design_counts_by_season: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
all_unique_standardized_seasons: Set[str] = set() # To track all unique seasons found

print("Aggregating design counts by designer/season/year...")
for sheet in csv_list:
    # Determine the number of rows based on a key column (e.g., 'Designer' or 'Season')
    # Assumes all relevant columns have the same length within a sheet
    num_rows = len(sheet.get("Designer", []))
    if num_rows == 0:
        continue # Skip empty sheets

    # Iterate through each row (design) in the sheet
    for i in range(num_rows):
        # Safely get designer and season for the current row
        designer_list = sheet.get("Designer", [])
        season_list = sheet.get("Season", [])

        if i < len(designer_list) and i < len(season_list):
            designer = designer_list[i].strip()
            season_original = season_list[i]

            # Skip if designer name is empty
            if not designer:
                continue

            # Standardize the season
            std_season_with_year = standardize_season(season_original)

            # Increment count if season format is valid
            if std_season_with_year != "unknown_format":
                design_counts_by_season[std_season_with_year][designer] += 1
                all_unique_standardized_seasons.add(std_season_with_year) # Track unique keys
        # else: # Handle potentially inconsistent row lengths if necessary
        #     print(f"Warning: Row index {i} out of bounds for designer/season list in a sheet.")


# 3. Chart Generation (Stratified by Designer, Proportional Stacks)
print("\n--- Generating Stratified Chart (Proportional Stacks by Designer) ---")

plot_data_long = [] # List to hold data for the long format DataFrame
# Define the desired order of seasons for plotting on the x-axis
season_order_list = [
    'spring', 'summer', 'pre-fall', 'fall', 'winter',
    'resort', 'couture',
    'unknown_term', 'year_only' # Catch-all for others/errors/edge cases
]

# Prepare data in long format: one row per designer per season/year with design count
print("Preparing data for plotting...")
# Iterate through the aggregated counts
for season_year_key, designer_counts in design_counts_by_season.items():
    # Re-extract year (as int) and term for sorting/structuring
    year_match = re.search(r'\b(\d{4})\b', season_year_key)
    term = season_year_key # Default if parsing fails
    year = None # Use numeric year

    if year_match:
        year_str = year_match.group(1)
        try:
            year = int(year_str)
        except ValueError:
            year = None # Skip if year is not convertible to int

        # Isolate the term part, handling potential edge cases
        term = re.sub(r'\b' + re.escape(year_str) + r'\b', '', season_year_key).strip()
        term = re.sub(r'^[/\s-]+|[/\s-]+$', '', term).strip()
        if not term or term == "unknown_term" or term == "year_only":
            term = "unknown_term" # Consolidate edge cases if needed

    # Only include if we have a valid numeric year and a recognized term
    if year is not None and term != "unknown_format":
        # Add an entry for each designer found in this season/year
        for designer, count in designer_counts.items():
            plot_data_long.append({
                'Year': year,                   # Numeric year for sorting
                'SeasonTerm': term,             # Standardized distinct term
                'SeasonYearKey': season_year_key, # Combined key for plot index
                'Designer': designer,
                'Count': count                  # Use the actual design count
            })

# Check if there is data to plot
if not plot_data_long:
    print("No valid data found to generate a stratified chart.")
else:
    # Create Long DataFrame
    df_long = pd.DataFrame(plot_data_long)

    # Convert SeasonTerm to an ordered categorical type for sorting x-axis correctly
    present_terms = df_long['SeasonTerm'].unique()
    ordered_categories = [t for t in season_order_list if t in present_terms]
    season_cat_type = CategoricalDtype(categories=ordered_categories, ordered=True)
    df_long['SeasonTerm'] = df_long['SeasonTerm'].astype(season_cat_type)

    # Sort data primarily by Year (numeric), then by the ordered SeasonTerm
    df_long.sort_values(by=['Year', 'SeasonTerm'], inplace=True)

    # Check number of unique designers - warn if high
    unique_designers = df_long['Designer'].nunique()
    print(f"Total unique designers to plot as stacks: {unique_designers}")
    if unique_designers > 40:
         print("Warning: High number of unique designers (>40) may lead to a visually cluttered chart.")
         print("Colors will repeat significantly, making individual designer identification difficult.")
    elif unique_designers == 0:
         print("No designers found in the filtered data. Cannot plot.")
         exit()

    # Pivot for plotting: Index = SeasonYearKey, Columns = Designer, Values = Count (design count)
    print("Pivoting data for chart...")
    try:
        pivot_df = df_long.pivot_table(index='SeasonYearKey',
                                       columns='Designer',
                                       values='Count', # Use actual design count here
                                       fill_value=0)

        # Ensure pivot table's index order matches the sorted DataFrame's key order
        sorted_keys = df_long['SeasonYearKey'].unique()
        pivot_df = pivot_df.reindex(sorted_keys)

        # --- Create Stacked Bar Chart ---
        print("Generating plot...")
        num_bars = len(sorted_keys)
        fig_width = max(15, num_bars * 0.5)
        fig_height = 10
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        cmap = 'turbo' # Colormap choice
        pivot_df.plot(kind='bar',
                      stacked=True,
                      ax=ax,
                      legend=False, # Legend still unusable
                      colormap=cmap,
                      width=0.8)

        # --- Customize the plot ---
        chart_title = (f'Total Designs per Season/Year (Stacked by Designer - {unique_designers} total)')
        ax.set_title(chart_title, fontsize=16, wrap=True)
        ax.set_xlabel('Season & Year', fontsize=12)
        # UPDATE Y-axis label to reflect design count
        ax.set_ylabel('Total Designs (Stacked by Designer)', fontsize=12)

        label_fontsize = max(6, 12 - num_bars // 10)
        ax.tick_params(axis='x', rotation=90, labelsize=label_fontsize)
        ax.tick_params(axis='y', labelsize=10)

        ax.yaxis.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.7)
        ax.set_axisbelow(True)

        if unique_designers > 20:
             plt.text(0.5, -0.3,
                      'Note: Legend omitted due to high number of designers. Colors will repeat.',
                      ha='center', va='center', transform=ax.transAxes, fontsize=9, color='grey')

        plt.tight_layout(rect=[0, 0.05, 1, 0.96])
        print("Displaying chart...")
        plt.show()

    except pd.errors.InvalidIndexError as e:
         print(f"\nError reindexing pivot table. Mismatch between sorted keys and pivot index? Error: {e}")
         # Add more debug info if needed
    except Exception as e:
        print(f"\nAn unexpected error occurred during plotting: {e}")


print("\nScript finished.")
