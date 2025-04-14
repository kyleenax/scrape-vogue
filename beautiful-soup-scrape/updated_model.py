import pandas as pd
import numpy as np
import random
from collections import defaultdict, Counter
import os

# === Load and preprocess === #
df = pd.read_csv('combined_sorted_fashion.csv')
df['Year'] = df['Season'].str.extract(r'(\d{4})').astype(float)
df['SeasonName'] = df['Season'].str.extract(r'(Fall|Spring)')
df.dropna(subset=['Year', 'SeasonName'], inplace=True)

cols_to_split = ['Garments', 'Accessories', 'Silhouette', 'Style Keywords', 'Notes']

def split_items(cell):
    if pd.isna(cell): return []
    return [item.strip() for item in str(cell).split(',') if item.strip()]

for col in cols_to_split:
    df[col] = df[col].apply(split_items)

# === Train/Test Split by Year === #
unique_years = sorted(df['Year'].unique())
split_idx = int(len(unique_years) * 0.8)
train_years = unique_years[:split_idx]
test_years = unique_years[split_idx:]

train_df = df[df['Year'].isin(train_years)]
test_df = df[df['Year'].isin(test_years)]

# === Balance the Training Set by Gender === #
min_count = min(
    len(train_df[train_df['Gender Presentation'] == 'Feminine']),
    len(train_df[train_df['Gender Presentation'] == 'Masculine']),
    len(train_df[train_df['Gender Presentation'] == 'Neutral'])
)

balanced_train_df = pd.concat([
    train_df[train_df['Gender Presentation'] == g].sample(n=min_count, random_state=42)
    for g in ['Feminine', 'Masculine', 'Neutral']
])

# === Build Frequency Tables === #
def build_freqs(dataframe):
    freqs = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    for _, row in dataframe.iterrows():
        gender = row['Gender Presentation']
        season = row['SeasonName']
        for col in cols_to_split:
            freqs[gender][season][col].update(row[col])
    return freqs

train_freqs = build_freqs(balanced_train_df)

def normalize(counter):
    total = sum(counter.values())
    return {k: v / total for k, v in counter.items()} if total > 0 else {}

probs = defaultdict(lambda: defaultdict(dict))
max_probs = defaultdict(lambda: defaultdict(dict))

for gender in train_freqs:
    for season in train_freqs[gender]:
        for col in cols_to_split:
            probs_dict = normalize(train_freqs[gender][season][col])
            sorted_probs = sorted(probs_dict.values(), reverse=True)
            avg_top = max(sorted_probs) if sorted_probs else 1e-6
            max_probs[gender][season][col] = avg_top
            probs[gender][season][col] = probs_dict

# === Sample Outfit with Scaled Confidence === #
def sample_outfit(gender, season, probs, max_probs, train_df):
    outfit = {}
    scaled_probs = []

    for col in cols_to_split:
        col_probs = probs[gender][season][col]
        if not col_probs:
            outfit[col] = []
            continue

        filtered_items = [(item, prob) for item, prob in col_probs.items() if prob > 0.001]
        if not filtered_items:
            outfit[col] = []
            continue

        items = [item for item, _ in filtered_items]
        weights = [prob for _, prob in filtered_items]
        if not items or not weights:
            outfit[col] = []
            continue

        rows = train_df[(train_df['Gender Presentation'] == gender) & (train_df['SeasonName'] == season)]
        item_count = round(np.mean([len(row[col]) for _, row in rows.iterrows()])) if not rows.empty else 3

        chosen = random.choices(items, weights=weights, k=item_count)
        outfit[col] = chosen

        max_col_prob = max_probs[gender][season].get(col, 1e-6)
        for item in chosen:
            p = col_probs.get(item, 1e-6)
            scaled_probs.append(p / max_col_prob)

    confidence = sum(scaled_probs) / len(scaled_probs) if scaled_probs else 0
    return outfit, round(confidence, 4)

# === Generate 6 Outfits === #
generated_outfits = []
for gender in ['Feminine', 'Masculine', 'Neutral']:
    for season in ['Fall', 'Spring']:
        print(f"Checking {gender} {season}...")
        if probs[gender][season]:
            outfit, confidence = sample_outfit(gender, season, probs, max_probs, balanced_train_df)
            row = {
                'Gender': gender,
                'Season': season,
                'Confidence': confidence
            }
            for col in cols_to_split:
                row[col] = ', '.join(outfit[col])
            generated_outfits.append(row)

# === Save to CSV === #
results_df = pd.DataFrame(generated_outfits)
os.makedirs('results', exist_ok=True)
results_df.to_csv('results/predicted-looks.csv', index=False)

print("✅ Generated outfits saved to results/predicted-looks.csv")
