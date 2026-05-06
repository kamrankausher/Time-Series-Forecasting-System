import pandas as pd
import numpy as np
import os
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error
from data_preprocessing import load_and_preprocess_data, split_data
from models import SarimaModel, ProphetModel, XGBoostModel, LSTMModel

def evaluate_model(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return mae, rmse

def main():
    print("Loading and preprocessing data...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'Forecasting Case- Study.xlsx')
    df = load_and_preprocess_data(file_path)    
    
    saved_models_dir = os.path.join(base_dir, 'saved_models')
    os.makedirs(saved_models_dir, exist_ok=True)
    
    states = df['State'].unique()
    best_models_info = {}
    
    for state in states:
        print(f"--- Training models for {state} ---")
        state_df = df[df['State'] == state].copy()
        
        train_df, val_df = split_data(state_df, test_weeks=8)
        
        if len(train_df) < 20:
            print(f"Not enough data for {state}, skipping.")
            continue
            
        models = {
            'SARIMA': SarimaModel(),
            'Prophet': ProphetModel(),
            'XGBoost': XGBoostModel(),
            'LSTM': LSTMModel()
        }
        
        best_model_name = None
        best_rmse = float('inf')
        
        for name, model in models.items():
            try:
                model.fit(train_df, target_col='Total')
                preds = model.predict(periods=8)
                
                if np.isnan(preds).any() or len(preds) != 8:
                    print(f"{name} failed or gave NaN predictions.")
                    continue
                    
                mae, rmse = evaluate_model(val_df['Total'].values, preds)
                print(f"  {name} - MAE: {mae:.2f}, RMSE: {rmse:.2f}")
                
                if rmse < best_rmse:
                    best_rmse = rmse
                    best_model_name = name
            except Exception as e:
                print(f"  {name} failed to train/predict: {e}")
        
        if best_model_name:
            print(f"Best model for {state} is {best_model_name} with RMSE {best_rmse:.2f}")
            
            if best_model_name == 'SARIMA':
                best_model = SarimaModel()
            elif best_model_name == 'Prophet':
                best_model = ProphetModel()
            elif best_model_name == 'XGBoost':
                best_model = XGBoostModel()
            elif best_model_name == 'LSTM':
                best_model = LSTMModel()
                
            best_model.fit(state_df, target_col='Total')
            
            model_path = os.path.join(saved_models_dir, f"{state.replace(' ', '_')}_model.joblib")
            joblib.dump(best_model, model_path)
            
            best_models_info[state] = {
                'model_name': best_model_name,
                'rmse': float(best_rmse),
                'path': model_path,
                'last_date': state_df['Date'].max().strftime('%Y-%m-%d')
            }
        else:
            print(f"No valid model found for {state}")
            
    joblib.dump(best_models_info, os.path.join(saved_models_dir, 'model_metadata.joblib'))
    print("Training complete and models saved.")

if __name__ == '__main__':
    main()
