import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import re

# Load dataset
df = pd.read_csv("combined_sorted_fashion.csv")

# Clean unnecessary columns
df = df.drop(columns=[col for col in df.columns if "Unnamed" in col])

# Drop rows with missing target
df = df.dropna(subset=["Style Keywords"])

# Fill missing text/categorical values
text_columns = ["Garments", "Accessories", "Notes"]
categorical_columns = ["Designer", "Season", "Gender Presentation", "Silhouette"]
df[text_columns] = df[text_columns].fillna("")
df[categorical_columns] = df[categorical_columns].fillna("Unknown")

# Extract numeric year from 'Season' column
df["Year"] = df["Season"].apply(lambda x: int(re.search(r"\d{4}", str(x)).group()) if pd.notnull(x) and re.search(r"\d{4}", str(x)) else None)

# Define training data (before 2021) and test data (2021 and after)
train_df = df[df["Year"] < 2021]
test_df = df[df["Year"] >= 2021]

# Target and features
target = "Style Keywords"
features = ["Designer", "Season", "Gender Presentation", "Garments", "Accessories", "Silhouette", "Notes"]

# Preprocessing
text_features = ["Garments", "Accessories", "Notes"]
categorical_features = ["Designer", "Season", "Gender Presentation", "Silhouette"]

preprocessor = ColumnTransformer(
    transformers=[
        ("text_garments", TfidfVectorizer(), "Garments"),
        ("text_accessories", TfidfVectorizer(), "Accessories"),
        ("text_notes", TfidfVectorizer(), "Notes"),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ]
)

# Pipeline
pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(max_iter=1000))
])

# Fit model on pre-2021
X_train = train_df[features]
y_train = train_df[target]
pipeline.fit(X_train, y_train)

# Predict on 2021–2024 data
X_test = test_df[features]
y_test = test_df[target]
y_pred = pipeline.predict(X_test)

# Evaluate
print("🔮 Forecast Evaluation: Predicting Style Keywords for 2021–2024 looks")
print(classification_report(y_test, y_pred))
