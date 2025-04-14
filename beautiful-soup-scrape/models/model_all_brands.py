import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import os

### 1. Load Data
df = pd.read_csv('final.csv')

# Extract year and season name
df['Year'] = df['Season'].str.extract(r'(\d{4})').astype(float)
df['SeasonName'] = df['Season'].str.extract(r'(Fall|Spring)')
df.dropna(subset=['Year', 'SeasonName'], inplace=True)

### 2. Preprocess multi-item columns
cols_to_split = ['Garments', 'Accessories', 'Silhouette', 'Style Keywords', 'Notes']

def split_items(cell):
    if pd.isna(cell): return []
    return [item.strip() for item in str(cell).split(',') if item.strip()]

for col in cols_to_split:
    df[col] = df[col].apply(split_items)

### 3. Train-Test Split by Year (80/20)
unique_years = sorted(df['Year'].unique())
split_idx = int(len(unique_years) * 0.8)
train_years = unique_years[:split_idx]
test_years = unique_years[split_idx:]

train_df = df[df['Year'].isin(train_years)]
test_df = df[df['Year'].isin(test_years)]

### 4. Build Frequency Tables
def build_freqs(dataframe):
    freqs = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    for _, row in dataframe.iterrows():
        gender = row['Gender Presentation']
        season = row['SeasonName']
        for col in cols_to_split:
            freqs[gender][season][col].update(row[col])
    return freqs

train_freqs = build_freqs(train_df)

def normalize(counter):
    total = sum(counter.values())
    return {k: v / total for k, v in counter.items()} if total > 0 else {}

probs = defaultdict(lambda: defaultdict(dict))
for gender in train_freqs:
    for season in train_freqs[gender]:
        for col in cols_to_split:
            probs[gender][season][col] = normalize(train_freqs[gender][season][col])

### 5. Sample Outfits
def sample_outfit(gender, season, probs, train_df):
    outfit = {}
    total_probs = []
    
    for col in ['Garments', 'Accessories', 'Silhouette', 'Style Keywords', 'Notes']:
        col_probs = probs[gender][season][col]
        if not col_probs:
            outfit[col] = []
            continue
        
        sorted_items = sorted(col_probs.items(), key=lambda x: x[1], reverse=True)

        # Estimate typical number of items to include
        rows = train_df[(train_df['Gender Presentation'] == gender) & (train_df['SeasonName'] == season)]
        item_count = round(np.mean([len(row[col]) for _, row in rows.iterrows()])) if not rows.empty else 3

        chosen = [item for item, _ in sorted_items[:item_count]]
        outfit[col] = chosen

        # Collect individual probabilities for averaging
        total_probs.extend([col_probs.get(item, 1e-6) for item in chosen])

    # Use average probability as confidence
    confidence = sum(total_probs) / len(total_probs) if total_probs else 0
    return outfit, round(confidence, 4)


### 6. Generate & Export Looks
generated_outfits = []
for gender in ['Feminine', 'Masculine', 'Neutral']:
    for season in ['Fall', 'Spring']:
        if probs[gender][season]:
            outfit, confidence = sample_outfit(gender, season, probs, train_df)
            row = {
                'Gender': gender,
                'Season': season,
                'Confidence': confidence
            }
            for col in cols_to_split:
                row[col] = ', '.join(outfit[col])
            generated_outfits.append(row)

result_df = pd.DataFrame(generated_outfits)

# Ensure results folder exists
os.makedirs('results', exist_ok=True)

# Save to CSV
result_df.to_csv('results/predicted-looks.csv', index=False)

print("✅ Saved predicted outfits to results/predicted-looks.csv")
