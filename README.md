# Time Series Forecasting System

## Objective
Build a production-ready forecasting system that:
1. Trains multiple forecasting algorithms
2. Compares and selects the best model
3. Exposes predictions via a REST API
4. Is designed like a real backend service

## Dataset and Problem Statement
Forecast the next 8 weeks of sales for each state using historical data. The dataset contains sales broken down by State and Category (Beverages). The data spans from 2019 to 2023.

## Implementation Details
The project is built using Python with a structured architecture separating concerns:
- **`src/data_preprocessing.py`**: Handles loading, missing date imputation by resampling to weekly frequency (`W-MON`), missing value interpolation, and extensive feature engineering.
    - Features generated: `lag_1`, `lag_7`, `lag_30`, `rolling_mean_4`, `rolling_std_4`, `day_of_week`, `month`, and `holiday_flag`.
- **`src/models.py`**: Implements 4 algorithms wrapped in a common interface with `.fit()` and `.predict()` methods.
    - **SARIMA** (statsmodels)
    - **Prophet** (Facebook Prophet)
    - **XGBoost** (Autoregressive approach with lag features)
    - **LSTM** (Deep learning using PyTorch)
- **`src/train.py`**: The orchestration script that trains all models for each state on a training split, evaluates on a validation set of 8 weeks using RMSE and MAE, automatically selects the best model per state, retrains it on the entire dataset, and saves it to disk via `joblib`.
- **`src/api.py`**: FastAPI application that exposes a `/forecast` endpoint to serve predictions using the best saved models.

## 🚀 How to Run Locally (VS Code, Cursor, or any Terminal)

Follow these exact steps to run the complete Time Series Forecasting pipeline locally. This guide assumes you have Python installed on your system.

### Step 1: Open the Project
1. Open your code editor (e.g., Visual Studio Code).
2. Open the project folder: `Time Series Forecasting System`.
3. Open an integrated terminal in your editor (In VS Code: `Ctrl+Shift+\``) and ensure you are in the project's root directory.

### Step 2: Set Up a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(Note: If you encounter an execution policy error, run `Set-ExecutionPolicy Unrestricted -Scope CurrentUser` as Administrator first, or use Command Prompt `cmd` and run `venv\Scripts\activate.bat`)*

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

*When successfully activated, you will see a `(venv)` prefix in your terminal prompt.*

### Step 3: Install Dependencies
Install all required packages (FastAPI, Prophet, PyTorch, XGBoost, etc.) by running:
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Training Pipeline
The training script will iterate through all states, train all four models (SARIMA, Prophet, XGBoost, LSTM), select the best one based on RMSE, and save the `.joblib` files to the `saved_models/` folder.
```powershell
python src/train.py
```
*(Note: Depending on your system, training may take several minutes. Pre-trained models might already exist in `saved_models/` from previous runs.)*

### Step 5: Start the API Server
Start the backend server that serves the forecasts:
```powershell
uvicorn src.api:app --reload
```
Wait until you see the message: `Uvicorn running on http://127.0.0.1:8000` 
*Your server is now live and waiting for requests!*

### Step 6: Test the API
You can test the API in different ways while the server is running:

**Method A: Using the Automated Test Scripts**
1. Open a **second** terminal window in your editor (leaving the server running in the first).
2. Activate your virtual environment in this new terminal.
3. Run one of the provided test scripts:
   ```powershell
   python test_api.py
   
   # Or to test specific non-LSTM models:
   python test_non_lstm.py
   ```
4. You will see the predictions printed directly in your console.

**Method B: Using the Interactive Web UI (Swagger)**
1. Open your web browser (Chrome, Edge, etc.).
2. Navigate to: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
3. This opens an interactive Swagger UI. Click on the green **POST /forecast** block.
4. Click the **Try it out** button on the right.
5. In the Request body box, edit the JSON to specify a state. For example:
   ```json
   {
     "state": "Texas",
     "periods": 8
   }
   ```
6. Click the large blue **Execute** button. Scroll down to see the real-time forecast response containing the predicted sales values!

## Using the API via HTTP / cURL

The API exposes a POST endpoint `/forecast` that requires the state name and (optionally) the number of periods (default 8).

**Example Request:**
```http
POST http://localhost:8000/forecast
Content-Type: application/json

{
    "state": "Alabama",
    "periods": 8
}
```

**Example Response:**
```json
{
    "state": "Alabama",
    "model_used": "XGBoost",
    "forecast_dates": [
        "2023-12-11",
        "2023-12-18",
        "..."
    ],
    "forecast_values": [
        256000000.0,
        248000000.0,
        "..."
    ]
}
```
