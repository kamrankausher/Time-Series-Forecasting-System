import urllib.request
import urllib.error
import json

states_to_test = ['Alabama', 'California', 'New York']

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
        print(f"Forecast dates: {output['forecast_dates']}")
        print(f"Forecast values: {output['forecast_values']}\n")
    except urllib.error.HTTPError as e:
        print(f"Error for {state}:")
        print(e.read().decode())
