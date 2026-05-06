from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os
import sys

# Fix for Windows DLL initialization errors (especially with PyTorch)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from fastapi.middleware.cors import CORSMiddleware

# Add src to path so models can be found by joblib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Time Series Forecasting System API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model metadata
try:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metadata_path = os.path.join(base_dir, 'saved_models', 'model_metadata.joblib')
    if os.path.exists(metadata_path):
        model_metadata = joblib.load(metadata_path)
    else:
        model_metadata = {}
except Exception as e:
    print(f"Failed to load metadata: {e}")
    model_metadata = {}

class ForecastRequest(BaseModel):
    state: str
    periods: int = 8

class ForecastResponse(BaseModel):
    state: str
    model_used: str
    forecast_dates: list
    forecast_values: list

    model_config = {
        "protected_namespaces": ()
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to the Time Series Forecasting API. Use /forecast to get predictions."}

@app.post("/forecast", response_model=ForecastResponse)
def get_forecast(request: ForecastRequest):
    state = request.state
    periods = request.periods
    
    if state not in model_metadata:
        raise HTTPException(status_code=404, detail=f"No model found for state: {state}")
        
    info = model_metadata[state]
    model_path = info['path']
    model_name = info['model_name']
    last_date = pd.to_datetime(info['last_date'])
    
    if not os.path.exists(model_path):
        raise HTTPException(status_code=500, detail="Model file missing on server.")
        
    try:
        model = joblib.load(model_path)
        predictions = model.predict(periods=periods)
        
        # Generate future dates (weekly W-MON)
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=7), periods=periods, freq='W-MON')
        
        return ForecastResponse(
            state=state,
            model_used=model_name,
            forecast_dates=[d.strftime('%Y-%m-%d') for d in future_dates],
            forecast_values=predictions.tolist()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making prediction: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    print("Run using: uvicorn api:app --reload")
