import pandas as pd
import re
import unicodedata

def normalize_brand_name(brand_name):
    """Convert special characters (e.g., ç → c, é → e) to plain ASCII letters."""
    normalized = unicodedata.normalize('NFKD', brand_name)
    return "".join(c for c in normalized if c.isascii())

def append_brands_to_urls(input_csv, output_csv):
    # ✅ Load the CSV
    df = pd.read_csv(input_csv)

    # ✅ Initialize an empty list to store the reformatted data
    formatted_data = []

    # ✅ Iterate through each row in the dataset
    for _, row in df.iterrows():
        season = row["season"]
        base_url = row["url"]
        brands = row["sampled_brands"]

        # ✅ Split brands into a list (keep original format)
        if pd.notna(brands):  # Check if brands exist
            brand_list = brands.split(",")  # Keep brand names unchanged

            # ✅ Append each brand with the updated URL
            for brand in brand_list:
                brand_clean = brand.strip()  # Keep original format

                # ✅ Normalize brand name (remove accents & special characters)
                brand_url_part = normalize_brand_name(brand_clean)
                
                # ✅ Format brand name for URL
                brand_url_part = brand_url_part.lower().replace(" ", "-").replace(".", "-")

                # ✅ Ensure no double hyphens ("--")
                brand_url_part = re.sub(r"-+", "-", brand_url_part)  # Replace multiple hyphens with a single one
                
                # ✅ Construct the updated URL
                updated_url = f"{base_url}/{brand_url_part}"

                formatted_data.append({
                    "season": season,
                    "url": updated_url,
                    "brand": f" {brand_clean}"  # Add space before brand name in CSV
                })

    # ✅ Convert list to DataFrame
    formatted_df = pd.DataFrame(formatted_data)

    # ✅ Save to a new CSV file
    formatted_df.to_csv(output_csv, index=False)
    print(f"✅ Reformatted data saved to {output_csv}")

# ✅ Run the function
append_brands_to_urls("sampled_v4.csv", "tidy_sampled_v4.csv")
