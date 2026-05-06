import pandas as pd
import numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar

def load_and_preprocess_data(file_path):
    # Load data
    df = pd.read_excel(file_path)
    
    # Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # We will process per state
    states = df['State'].unique()
    processed_dfs = []
    
    cal = calendar()
    holidays = cal.holidays(start=df['Date'].min(), end=df['Date'].max())
    
    for state in states:
        state_df = df[df['State'] == state].copy()
        
        # Sort by date
        state_df = state_df.sort_values('Date')
        
        # Set Date as index
        state_df.set_index('Date', inplace=True)
        
        # Resample to weekly frequency (W-MON) to handle missing dates and regularize frequency
        # Assuming Total is sales, we sum them up per week
        state_df = state_df[['Total']].resample('W-MON').sum()
        
        # Handle missing values (if any after resampling, though sum() returns 0 for missing weeks)
        # We replace 0s with interpolation or leave them as 0 if it implies no sales.
        # But sum() on empty bins returns 0. Let's keep 0 or interpolate.
        state_df['Total'] = state_df['Total'].replace(0, np.nan)
        state_df['Total'] = state_df['Total'].interpolate(method='linear').fillna(0)
        
        # Feature Engineering
        # Lag features: t-1, t-7, t-30
        state_df['lag_1'] = state_df['Total'].shift(1)
        state_df['lag_7'] = state_df['Total'].shift(7)
        state_df['lag_30'] = state_df['Total'].shift(30)
        
        # Rolling mean / std (using 4 weeks as a proxy for a month)
        state_df['rolling_mean_4'] = state_df['Total'].rolling(window=4).mean()
        state_df['rolling_std_4'] = state_df['Total'].rolling(window=4).std()
        
        # Day of week, month
        # Since it's weekly, day of week is always the same (Monday). Let's just extract it to fulfill requirement,
        # but month is more useful.
        state_df['day_of_week'] = state_df.index.dayofweek
        state_df['month'] = state_df.index.month
        
        # Holiday flag
        # Check if any day in the week is a holiday
        state_df['holiday_flag'] = state_df.index.isin(holidays).astype(int)
        
        # Drop NaN values caused by shifting
        # state_df.dropna(inplace=True)  # We will drop NaNs during modeling to not lose recent data for future predictions
        
        state_df['State'] = state
        processed_dfs.append(state_df.reset_index())
        
    final_df = pd.concat(processed_dfs, ignore_index=True)
    return final_df

def split_data(state_df, test_weeks=8):
    """
    Train/validation split using time series logic (no leakage).
    """
    # Sort by date just in case
    state_df = state_df.sort_values('Date')
    
    # The last 'test_weeks' will be used for validation/testing
    train = state_df.iloc[:-test_weeks]
    test = state_df.iloc[-test_weeks:]
    
    return train, test

if __name__ == '__main__':
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'Forecasting Case- Study.xlsx')
    df = load_and_preprocess_data(file_path)
    print("Processed Data Shape:", df.shape)
    print("Columns:", df.columns)
    print(df.head(35))
