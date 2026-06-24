import pandas as pd
import time
import json
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
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
# RANDOM FOREST PIPELINE
# -----------------------------
model = Pipeline([
    ("prep", preprocess),
    ("rf", RandomForestRegressor(random_state=42))
])

# -----------------------------
# HYPERPARAMETER GRID
# -----------------------------
param_grid = {
    "rf__n_estimators": [200],
    "rf__max_depth": [12, 15, 18],
    "rf__min_samples_split": [2, 5],
}

# -----------------------------
# GRID SEARCH FOR BEST PARAMS
# -----------------------------
grid = GridSearchCV(model, param_grid, scoring="r2", cv=3, n_jobs=-1)
grid.fit(X, y)

best_model = grid.best_estimator_

# -----------------------------
# TRAIN-TEST SPLIT & FINAL TRAIN
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
best_model.fit(X_train, y_train)
pred = best_model.predict(X_test)

# -----------------------------
# METRICS
# -----------------------------
r2 = r2_score(y_test, pred)
mae = mean_absolute_error(y_test, pred)
accuracy = r2 * 100
elapsed = time.time() - start

# -----------------------------
# PRINT RESULTS
# -----------------------------
print("\n🥕 VEGETABLE PRICE RF MODEL RESULTS")
print(f"✅ Best Parameters: {grid.best_params_}")
print(f"🎯 Accuracy: {accuracy:.2f}%")
print(f"📉 Mean Absolute Error: {mae:.2f}")
print(f"⏱ Time Taken: {elapsed:.2f} sec")

# -----------------------------
# SAVE MODEL
# -----------------------------
joblib.dump(best_model, "rf_vegetable.pkl")
print("\n💾 Model Saved: rf_vegetable.pkl")

# -----------------------------
# SAVE RESULTS TO JSON
# -----------------------------
results = {
    "Model": "Random Forest",
    "Dataset": "Vegetable",
    "Best_Parameters": grid.best_params_,
    "R2_Score": round(r2, 4),
    "Accuracy(%)": round(accuracy, 2),
    "MAE": round(mae, 4),
    "Time_Taken(s)": round(elapsed, 2)
}

output_file = "model_results_vegetable_rf.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=4)

print(f"📊 Results saved to {output_file}")
