import urllib.request
import urllib.error
import json

# Test states that don't use LSTM (Alabama uses Prophet, Florida uses SARIMA, Tennessee uses XGBoost)
states_to_test = ['Alabama', 'Florida', 'Tennessee']

print("Starting API testing for non-LSTM models...")

for state in states_to_test:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/forecast', 
        method='POST', 
        headers={'Content-Type': 'application/json'}, 
        data=json.dumps({'state': state, 'periods': 8}).encode('utf-8')
    )

    try:
        res = urllib.request.urlopen(req)
        print(f"--- Forecast for {state} ---")
        output = json.loads(res.read().decode())
        print(f"Model used: {output['model_used']}")
        print(f"Forecast dates: {output['forecast_dates'][:3]} ...")
        print(f"Forecast values: {[round(v, 2) for v in output['forecast_values'][:3]]} ...\n")
    except urllib.error.HTTPError as e:
        print(f"Error for {state}:")
        print(e.read().decode())
    except Exception as e:
        print(f"Unexpected error for {state}: {e}")
