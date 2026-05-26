import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os

# Ensure we are in the right directory context
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'historical_prices.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'ml_model')

# 1. Load the historical property data
print("Loading data...")
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    print(f"Error: Could not find dataset at {DATA_PATH}")
    exit()

# 2. Data Preprocessing & Feature Engineering
# Machine learning models only understand numbers. 
# We must convert text categories (like 'Good' or 'Poor' Locality) into binary columns (1s and 0s).
df = pd.get_dummies(df, columns=['Locality_Quality'], drop_first=True)

# Separate the features (X) from the target we want to predict (y)
X = df.drop('Price', axis=1)
y = df['Price']

# Split the data: 80% for training the model, 20% for testing its accuracy
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Train the Random Forest Model
print("Training the Random Forest Regressor...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 4. Evaluate the Model's Performance
predictions = model.predict(X_test)
r2 = r2_score(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)

print("\n--- Model Evaluation ---")
print(f"R² Score: {r2:.2f} (1.0 is perfect)")
print(f"Mean Absolute Error (MAE): ₹{mae:,.2f}")
print("------------------------\n")

# 5. Export and Save the Model
# We save the model so the web backend can use it without retraining it every time.
model_path = os.path.join(MODEL_DIR, 'random_forest.pkl')
columns_path = os.path.join(MODEL_DIR, 'model_columns.pkl')

joblib.dump(model, model_path)
joblib.dump(list(X.columns), columns_path) # Save feature names for backend formatting

print(f"Success! Model saved to: {model_path}")