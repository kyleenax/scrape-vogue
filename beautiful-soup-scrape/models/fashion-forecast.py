import pandas as pd
import numpy as np
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MultiLabelBinarizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics.pairwise import cosine_similarity

# --- Load & Prepare Dataset ---
df = pd.read_csv("../models/final.csv")

# Clean up
text_columns = ["Garments", "Accessories", "Notes"]
categorical_columns = ["Designer", "Season", "Gender Presentation", "Silhouette"]
df[text_columns] = df[text_columns].fillna("")
df[categorical_columns] = df[categorical_columns].fillna("Unknown")
df = df.drop(columns=[col for col in df.columns if "Unnamed" in col])
df = df.dropna(subset=["Style Keywords"])

# Remove rows with empty text fields
df = df[~((df["Garments"] == "") & (df["Accessories"] == "") & (df["Notes"] == ""))]

# Extract year from 'Season'
df["Year"] = df["Season"].apply(lambda x: int(re.search(r"\d{4}", str(x)).group()) if pd.notnull(x) and re.search(r"\d{4}", str(x)) else None)

# Identify Top 10 Brands
top_brands = df["Designer"].value_counts().head(10).index.tolist()

# Convert 'Style Keywords' to multilabel format
df["Style Keyword List"] = df["Style Keywords"].apply(lambda x: [kw.strip().lower() for kw in str(x).split(",")])
mlb = MultiLabelBinarizer()
y_multilabel = mlb.fit_transform(df["Style Keyword List"])

# Features
features = ["Designer", "Season", "Gender Presentation", "Garments", "Accessories", "Silhouette", "Notes"]

# Preprocessing
preprocessor = ColumnTransformer([
    ("garments", TfidfVectorizer(), "Garments"),
    ("accessories", TfidfVectorizer(), "Accessories"),
    ("notes", TfidfVectorizer(), "Notes"),
    ("categoricals", OneHotEncoder(handle_unknown="ignore"), ["Designer", "Season", "Gender Presentation", "Silhouette"])
])

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", OneVsRestClassifier(LogisticRegression(max_iter=1000)))
])

# Train the model
train_df = df[df["Year"] < 2021]
X_train = train_df[features].dropna()
y_train = y_multilabel[train_df.index]
X_train = X_train[~((X_train["Garments"] == "") & (X_train["Accessories"] == "") & (X_train["Notes"] == ""))]
y_train = y_train[:len(X_train)]
pipeline.fit(X_train, y_train)

# Prepare real look vectors for similarity check
real_look_vectors = pipeline.named_steps['preprocessor'].transform(X_train)

# Output Directory
output_dir = "../models"
os.makedirs(output_dir, exist_ok=True)

# Forecast Generation (season-specific)
target_seasons = ["Spring 2025", "Fall 2025", "Spring 2026", "Fall 2026"]
genders = ["Feminine", "Masculine", "Androgynous"]

for brand in top_brands:
    for season in target_seasons:
        simulated_looks = []

        # Focus on matching brand AND season type (e.g. Spring only)
        historical_subset = df[(df["Designer"] == brand) & (df["Season"].str.contains(season.split()[0], case=False, na=False))]

        garments = historical_subset["Garments"].dropna().unique().tolist() or df["Garments"].dropna().unique().tolist()
        accessories = historical_subset["Accessories"].dropna().unique().tolist() or df["Accessories"].dropna().unique().tolist()
        notes = historical_subset["Notes"].dropna().unique().tolist() or df["Notes"].dropna().unique().tolist()
        silhouettes = historical_subset["Silhouette"].dropna().unique().tolist() or df["Silhouette"].dropna().unique().tolist()

        # Generate a pool of simulated looks specific to the season
        for _ in range(50):
            look = {
                "Designer": brand,
                "Season": season,
                "Gender Presentation": np.random.choice(genders),
                "Garments": np.random.choice(garments),
                "Accessories": np.random.choice(accessories),
                "Silhouette": np.random.choice(silhouettes),
                "Notes": np.random.choice(notes)
            }
            simulated_looks.append(look)

        sim_df = pd.DataFrame(simulated_looks)
        predicted_probs = pipeline.predict_proba(sim_df)
        predicted_binary = (predicted_probs >= 0.5).astype(int)

        # Compute style predictions and per-label confidence
        predicted_styles = []
        confidence_scores = []
        for i, probs in enumerate(predicted_probs):
            active_labels = []
            conf_dict = {}
            for j, label in enumerate(mlb.classes_):
                if predicted_binary[i][j] == 1:
                    active_labels.append(label)
                    conf_dict[label] = round(probs[j], 3)
            predicted_styles.append(", ".join(active_labels))
            confidence_scores.append(conf_dict)

        sim_df["Predicted Styles"] = predicted_styles
        sim_df["Confidence Scores"] = confidence_scores

        # Compute overall look-likelihood by cosine similarity to real looks
        sim_vectors = pipeline.named_steps['preprocessor'].transform(sim_df)
        similarities = cosine_similarity(sim_vectors, real_look_vectors)
        sim_df["Look Confidence"] = np.max(similarities, axis=1)

        # Select the top 3 most confident looks
        top_3 = sim_df.nlargest(3, "Look Confidence")

        # Save to CSV
        filename = f"{brand.replace(' ', '_')}_{season.replace(' ', '_')}_top_3_looks.csv"
        top_3.to_csv(os.path.join(output_dir, filename), index=False)

print("✅ Forecasting complete. Top 3 seasonal looks saved to 'models' directory.")
