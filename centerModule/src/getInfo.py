import requests
import json

def get_alerts(state):
    # headers = {'User-Agent' : 'mattyershov@gmail.com'}
    # endpoint = 'https://api.weather.gov/alerts/active/area/{state}'
    resp = requests.get('https://api.weather.gov/alerts/active/area/{state}', headers={'User-Agent' : 'mattyershov@gmail.com'})
    print(resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print(data['features'])
        return data['features']
    else:
        print("error")
        return None

def main():
    alerts = get_alerts("MA")


if (__name__ == "__main__"):
    main()