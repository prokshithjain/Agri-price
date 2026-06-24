import pandas as pd
import numpy as np
import time
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os

# -----------------------------
# START TIMER
# -----------------------------
start = time.time()

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_excel("Vegetables_Datasets.xlsx")

categorical = ["seasonality", "festival"]
numeric = ["transport_cost", "demand_index", "supply_index", "rainfall_level"]

X = df[categorical + numeric]
y = df["price"]

# -----------------------------
# PREPROCESSING
# -----------------------------
preprocess = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ("num", StandardScaler(), numeric)
])

# -----------------------------
# FIND BEST K VALUE
# -----------------------------
best_k = None
best_score = -999

for k in range(3, 31):
    model = Pipeline([
        ("prep", preprocess),
        ("knn", KNeighborsRegressor(n_neighbors=k))
    ])
    model.fit(X, y)
    pred = model.predict(X)
    score = r2_score(y, pred)
    if score > best_score:
        best_score = score
        best_k = k

# -----------------------------
# FINAL MODEL TRAINING
# -----------------------------
final_model = Pipeline([
    ("prep", preprocess),
    ("knn", KNeighborsRegressor(n_neighbors=best_k))
])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

final_model.fit(X_train, y_train)
pred = final_model.predict(X_test)

# -----------------------------
# METRICS
# -----------------------------
r2 = r2_score(y_test, pred)
mae = mean_absolute_error(y_test, pred)
accuracy = r2 * 100
elapsed = time.time() - start

print(f"\n✅ Best K: {best_k}")
print(f"🎯 Accuracy: {accuracy:.2f}%")
print(f"📉 Mean Absolute Error: {mae:.2f}")
print(f"⏱ Time Taken: {elapsed:.2f} seconds")

# -----------------------------
# SAVE MODEL
# -----------------------------
joblib.dump(final_model, "knn_vegetable.pkl")
print("💾 Model saved as knn_vegetable.pkl")

# -----------------------------
# SAVE RESULTS TO JSON
# -----------------------------
results = {
    "Model": "KNN",
    "Dataset": "Vegetable",
    "Best_K": best_k,
    "R2_Score": round(r2, 4),
    "Accuracy(%)": round(accuracy, 2),
    "MAE": round(mae, 4),
    "Time_Taken(s)": round(elapsed, 2)
}

output_file = "model_results_vegetable_knn.json"

with open(output_file, "w") as f:
    json.dump(results, f, indent=4)

print(f"📊 Results saved to {output_file}")
