import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from xgboost import XGBRegressor
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from sklearn.preprocessing import StandardScaler
    TORCH_AVAILABLE = True
    TORCH_ERROR = None
except Exception as e:
    TORCH_AVAILABLE = False
    TORCH_ERROR = str(e)
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
import warnings
warnings.filterwarnings("ignore")

class SarimaModel:
    def __init__(self, order=(1,1,1), seasonal_order=(1,1,0,52)):
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None

    def fit(self, df, target_col='Total'):
        endog = df[target_col].values
        self.model = SARIMAX(endog, order=self.order, seasonal_order=self.seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
        self.results = self.model.fit(disp=False)
        
    def predict(self, periods):
        forecast = self.results.forecast(steps=periods)
        return forecast

class ProphetModel:
    def __init__(self):
        self.model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)

    def fit(self, df, target_col='Total'):
        prophet_df = df.copy()
        prophet_df = prophet_df[['Date', target_col]].rename(columns={'Date': 'ds', target_col: 'y'})
        self.model.fit(prophet_df)
        
    def predict(self, periods):
        future = self.model.make_future_dataframe(periods=periods, freq='W-MON')
        forecast = self.model.predict(future)
        return forecast['yhat'].iloc[-periods:].values

class XGBoostModel:
    def __init__(self):
        self.model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
        self.features = ['lag_1', 'lag_7', 'lag_30', 'rolling_mean_4', 'rolling_std_4', 'day_of_week', 'month', 'holiday_flag']
        self.history = None
        self.target_col = None
        self.cal = calendar()

    def fit(self, df, target_col='Total'):
        self.target_col = target_col
        self.history = list(df[target_col].values)
        self.last_date = df['Date'].max()
        
        train_df = df.dropna(subset=self.features)
        X = train_df[self.features]
        y = train_df[target_col]
        self.model.fit(X, y)

    def predict(self, periods):
        predictions = []
        hist = self.history.copy()
        current_date = self.last_date
        
        for i in range(periods):
            current_date += pd.Timedelta(days=7)
            
            lag_1 = hist[-1] if len(hist) >= 1 else 0
            lag_7 = hist[-7] if len(hist) >= 7 else 0
            lag_30 = hist[-30] if len(hist) >= 30 else 0
            
            recent_4 = hist[-4:] if len(hist) >= 4 else hist
            rolling_mean_4 = np.mean(recent_4)
            rolling_std_4 = np.std(recent_4) if len(recent_4) > 1 else 0
            
            day_of_week = current_date.dayofweek
            month = current_date.month
            
            # Holiday flag
            holidays = self.cal.holidays(start=current_date, end=current_date)
            holiday_flag = 1 if len(holidays) > 0 else 0
            
            X_pred = pd.DataFrame([{
                'lag_1': lag_1,
                'lag_7': lag_7,
                'lag_30': lag_30,
                'rolling_mean_4': rolling_mean_4,
                'rolling_std_4': rolling_std_4,
                'day_of_week': day_of_week,
                'month': month,
                'holiday_flag': holiday_flag
            }])
            
            pred = self.model.predict(X_pred)[0]
            predictions.append(pred)
            hist.append(pred)
            
        return np.array(predictions)

if TORCH_AVAILABLE:
    class SimpleLSTM(nn.Module):
        def __init__(self, input_size=1, hidden_size=64, num_layers=1):
            super(SimpleLSTM, self).__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            out = self.fc(out[:, -1, :])
            return out

    class LSTMModel:
        def __init__(self, seq_length=8, epochs=100, lr=0.01):
            self.seq_length = seq_length
            self.epochs = epochs
            self.lr = lr
            self.model = SimpleLSTM()
            self.scaler = StandardScaler()
            self.history = None

        def fit(self, df, target_col='Total'):
            self.history = df[target_col].values
            scaled_data = self.scaler.fit_transform(self.history.reshape(-1, 1))
            
            X, y = [], []
            for i in range(len(scaled_data) - self.seq_length):
                X.append(scaled_data[i:i+self.seq_length])
                y.append(scaled_data[i+self.seq_length])
                
            if len(X) == 0:
                return # Not enough data
                
            X = torch.FloatTensor(np.array(X))
            y = torch.FloatTensor(np.array(y))
            
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
            
            for epoch in range(self.epochs):
                optimizer.zero_grad()
                outputs = self.model(X)
                loss = criterion(outputs, y)
                loss.backward()
                optimizer.step()

        def predict(self, periods):
            predictions = []
            if len(self.history) < self.seq_length:
                return np.zeros(periods)
                
            hist = list(self.scaler.transform(self.history[-self.seq_length:].reshape(-1, 1)).flatten())
            
            self.model.eval()
            with torch.no_grad():
                for i in range(periods):
                    X_pred = torch.FloatTensor(hist[-self.seq_length:]).view(1, self.seq_length, 1)
                    pred = self.model(X_pred).item()
                    predictions.append(pred)
                    hist.append(pred)
                    
            predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
            return predictions
else:
    class LSTMModel:
        def __init__(self, *args, **kwargs):
            pass
        def fit(self, *args, **kwargs):
            raise ImportError(f"LSTM model unavailable due to PyTorch error: {TORCH_ERROR}")
        def predict(self, *args, **kwargs):
            raise ImportError(f"LSTM model unavailable due to PyTorch error: {TORCH_ERROR}")
