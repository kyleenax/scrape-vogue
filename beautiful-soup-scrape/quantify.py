import pandas as pd
import os
from datetime import date
import datetime as dt


agg_df = None
path = os.path.join(os.getcwd(), "beautiful-soup-scrape", "final_brand_csvs")

for csv in os.listdir(path):
    csv_path = os.path.join(path, csv)
    if csv.endswith(".csv"):  # Ensure only CSV files are processed
        df = pd.read_csv(csv_path)
        df["Company"] = os.path.splitext(csv)[0]
        
        if agg_df is None:
            agg_df = df
        else:
            agg_df = pd.concat([agg_df, df], ignore_index=True)

# Display the first few rows of the aggregated DataFrame
print(agg_df.head())

def seasonstoDates(df):
    seasonsToDates = {}
    
    for season in df["Season"].unique():
        year = ''.join(filter(str.isdigit, season))
        time_of_year = ''.join(filter(lambda x: not x.isdigit(), season))
        year = int(year)
        if time_of_year.lower().strip().split(" ")[-1] in ["autumn", "fall", "aw"]:
            seasonsToDates[season] = date(year, 10, 15).strftime("%Y-%m-%d")  # Assuming Fall dates
        elif time_of_year.lower().strip() in ["spring"]: #Placeholder
            seasonsToDates[season] = date(year, 4, 15).strftime("%Y-%m-%d")  # Assuming Fall dates
        else:
            print(f"Missing Season {time_of_year} {year}")

    df["Season"] = df["Season"].map(seasonsToDates)  # Add Date column
    df["Season"] = pd.to_datetime(df["Season"], errors="coerce")

    # Format all dates as YYYY-MM-DD (ISO 8601)
    df["Season"] = df["Season"].dt.strftime("%Y-%m-%d")    
    return df

agg_df = seasonstoDates(agg_df)

def accessory_percentage(df, season, accessory, accessory_column):
    """Calculate the percentage of outfits that feature a given accessory in a specific season."""
    
    # Ensure "Season " and the accessory column exist
    if "Season" not in df.columns or accessory_column not in df.columns:
        print(f"Error: Missing required columns ('Season ' or '{accessory_column}') in DataFrame.")
        return 0
    
    season_df = df[df["Season"] == season]  # Filter by season
    total_outfits = len(season_df)
    
    if total_outfits == 0:
        return 0  # Avoid division by zero
    
    # Count outfits where the accessory column contains the keyword (case-insensitive)
    outfits_with_accessory = season_df[accessory_column].fillna("").str.contains(accessory, case=False, na=False).sum()
    
    return (outfits_with_accessory / total_outfits)

def gender_percentage(df, season, accessory, accessory_column, gender):
    """Calculate the percentage of outfits with a specific gender and accessory in a season."""
    
    season_df = df[df["Season"] == season]
    gender_df = season_df[season_df["Gender Presentation"].isin(gender)]
    total_outfits = len(gender_df)
    
    if total_outfits == 0:
        return 0
    
    outfits_with_accessory = gender_df[accessory_column].fillna("").str.contains(accessory, case=False, na=False).sum()
    
    return (outfits_with_accessory / total_outfits)

# List of accessory columns you want to analyze (you can add more here if needed)
accessory_columns = ["Accessories", "Garments", "Silhouette", "Style Keywords"]
results = []
# Iterate over each season
for season in agg_df["Season"].unique():
    # Iterate over each accessory column
    for accessory_column in accessory_columns:
        # Clean and split the accessories across columns
        accessories = agg_df[accessory_column].fillna("").str.replace(",", "").str.replace("\"", "").str.lower().str.replace(".", "").str.split(" ").explode().unique()
        accessories = [a.strip() for a in accessories if not a.endswith("s")]
        # Iterate over each accessory in the list and calculate the percentage
        for accessory in accessories:
            percentage = accessory_percentage(agg_df, season, accessory, accessory_column)  # Compute percentage
            
            # Calculate percentages for feminine and unisex
            feminine_percentage = gender_percentage(agg_df, season, accessory, accessory_column, ["Feminine"])
            unisex_percentage = gender_percentage(agg_df, season, accessory, accessory_column, ["Unisex", "Androgynous", "Gender Neutral"])
            masculine_percentage = gender_percentage(agg_df, season, accessory, accessory_column, ["Masculine"])

            results.append({
                "Season": season, 
                "Item": accessory, 
                "Item Type": accessory_column,
                "Percentage": percentage,
                "Percent Feminine": feminine_percentage,
                "Percent Unisex": unisex_percentage,
                "Percent Masculine": masculine_percentage
            })  # Store result

# Create DataFrame and sort by frequency (descending)
results_df = pd.DataFrame(results).sort_values(by="Percentage", ascending=False)

# Pivot the DataFrame to have separate columns for each item type
pivot_df = results_df.pivot_table(index=["Season", "Item", "Percent Feminine", "Percent Unisex", "Percent Masculine"], columns="Item Type", values="Percentage").reset_index()

print(pivot_df)
pivot_df.to_csv("fun.csv", index=False)