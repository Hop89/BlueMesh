import requests


def main():
    state = "MA"
    alert_api_url = f"https://api.weather.gov/alerts/active/area/{state}"
    alert_resp = requests.get(alert_api_url)
    print(alert_resp)