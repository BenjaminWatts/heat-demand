from pydantic import BaseModel
import pandas as pd
import requests, json

OUTPUT_VARIABLES = ["heatpump_outsideT", "heatpump_elec", "heatpump_heat"]
START_DATE = "2020-01-01"
END_DATE = '2024-11-21'
INTERVAL = 3600
index = pd.date_range(START_DATE, END_DATE, freq=f"{INTERVAL}S")

class Site(BaseModel):
    id: int
    userid: int
    published: int
    last_updated: int
    location: str
    url: str
    share: int
    hp_model: str
    hp_type: str
    hp_output: float
    flow_temp: float
    zone_number: int
    space_heat_control_type: str
    dhw_control_type: str
    dhw_target_temperature: float
    floor_area: float
    heat_demand: float
    heat_loss: float

    def check_download_data(self):
        if self.already_downloaded():
            return
        
        feeds = ",".join(OUTPUT_VARIABLES)
        url = f"https://heatpumpmonitor.org/timeseries/data?id={self.id}&feeds={feeds}&start={START_DATE}&end={END_DATE}&interval={INTERVAL}&average=1&timeformat=notime"
        resp = requests.get(url)
        df = pd.DataFrame(
            index=pd.date_range(START_DATE, END_DATE, freq=f"{INTERVAL}s"),
            data=resp.json()
        )
        df = df.dropna()
        # convert df to dict
        rows = []
        for i, row in df.iterrows():
            rows.append({
                "ts": int(i.timestamp()),
                "t": round(row["heatpump_heat"], 1),
                "e": int(row["heatpump_elec"]),
                "h": int(row["heatpump_heat"])
            })
        # write to file
        with open(f"data/{self.id}.json", "w") as f:
            json.dump({
                "site": self.model_dump(),
                "outputs": rows,    
            }, f)
            
    def already_downloaded(self):
        try:
            with open(f"data/{self.id}.json", "r") as f:
                return json.load(f)
        except:
            return False
            
    def get_file_fp(self):
        return f"data/{self.id}.json"