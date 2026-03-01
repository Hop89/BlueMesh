import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

WX_TOKEN = os.environ.get("WX_TOKEN")

def get_alerts():
    resp = requests.get(f'http://api.weatherapi.com/v1/alerts.json?key={WX_TOKEN}&q=Boston')
    print(resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print(data['alerts']['alert'])
        return(data['alerts']['alert'])
    else:
        print("error")
        return None

def main():
    alerts = get_alerts()


if (__name__ == "__main__"):
    main()