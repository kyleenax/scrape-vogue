import pandas as pd
import random

# Load the dataset (update filename if needed)
df = pd.read_csv('v4.csv')

# Check for correct column names
print(df.columns)

# Define function to sample up to 40 brands
def sample_brands(brand_string):
    if pd.isna(brand_string):
        return []
    # Split by comma and strip spaces
    brand_list = [brand.strip() for brand in brand_string.split(',')]
    return random.sample(brand_list, min(40, len(brand_list)))

# Apply sampling
df['sampled_brands'] = df['list-of-brands'].apply(sample_brands)

# Create new DataFrame
sampled_df = df[['season', 'url', 'sampled_brands']]

# Save to new CSV
sampled_df['sampled_brands'] = sampled_df['sampled_brands'].apply(lambda x: ', '.join(x))
sampled_df.to_csv('sampled_v4.csv', index=False)

# Preview
sampled_df.head()