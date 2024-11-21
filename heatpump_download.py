import requests, json
import pandas as pd
from pytypes import Site


def get_sites():
    url = "https://heatpumpmonitor.org/system/list/public.json"
    resp = requests.get(url)
    data = resp.json()
    sites = [Site(**site) for site in data]
    # write to sites.json
    with open("sites.json", "w") as f:
        json.dump(data, f)
    return sites
    
def get_all():
    sites = get_sites()
    for site in sites:
        try:
            site.check_download_data()
        except Exception as e:
            print(f"Error downloading {site.id}: {e}")


# url = 'https://heatpumpmonitor.org/timeseries/data?id=2&feeds=heatpump_outsideT&start=01-06-2024&end=02-06-2024&interval=3600&average=1&timeformat=notime'

if __name__ == "__main__":
    get_all()
    
    