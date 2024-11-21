import os
import json
import pandas as pd
from pytypes import Site
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable
import numpy as np

data_dir = 'data'

def list_files_in_dir():
    return os.listdir(data_dir)

class SiteOutputs(Site):
    def capacity_factor_series(self, outputs: pd.DataFrame) -> pd.Series:
        heatpump_capacity = self.hp_output
        cf = outputs['h'] / (heatpump_capacity * 1000)
        cf = cf.clip(0, 1)
        return cf.to_frame(name=self.id)

def open_sites():
    total_count = 0
    total_capacity = 0
    df = pd.DataFrame()

    for fp in list_files_in_dir():
        with open(f"{data_dir}/{fp}", "r") as f:
            contents = json.load(f)
            site = SiteOutputs(**contents["site"])
            outputs = pd.DataFrame(contents["outputs"])

            # Set 'ts' column as index and convert to datetime in Europe/London timezone
            if 'ts' in outputs.columns:
                outputs.set_index("ts", inplace=True)
                outputs.index = pd.to_datetime(outputs.index, unit="s").tz_localize("UTC").tz_convert("Europe/London")
                cf = site.capacity_factor_series(outputs)

                # Add to DataFrame, aligning columns and rows
                df = pd.concat([df, cf], axis=1)

                total_capacity += site.hp_output
                total_count += 1

    # Write combined DataFrame to file
    mean = df.mean(axis=1)

    # Group by month for plotting
    months = mean.groupby(mean.index.month).mean()
    plt.figure(figsize=(10, 6))
    plt.plot(months, marker='o')
    MONTHS_OF_YEAR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    plt.xticks(range(1, 13), MONTHS_OF_YEAR)
    plt.xlabel("Month")
    plt.ylabel("Capacity Factor")
    plt.title(f"Mean Capacity Factor for {total_count} UK Heat Pumps with Total Capacity {int(total_capacity)} kW")
    plt.savefig("month.png")
    plt.close()

    # Group by hour of day and month of year
    df['hour'] = df.index.hour  # Now reflects Europe/London local time
    df['month'] = df.index.month
    grouped = df.groupby(['month', 'hour']).mean().mean(axis=1).unstack(level=0)

    # Define a custom cyclic colormap for warmer summers and cooler winters
    winter_colors = plt.cm.Blues(np.linspace(0.4, 1, 6))  # Cool blues for winter months
    summer_colors = plt.cm.Oranges(np.linspace(0.4, 1, 6))  # Warm oranges for summer months
    colors = np.vstack((winter_colors[:3], summer_colors, winter_colors[3:]))  # Arrange by season
    month_colors = [colors[(month - 1) % 12] for month in range(1, 13)]  # Ensure cyclic transition

    # Plot each month as a separate line with corresponding color
    plt.figure(figsize=(12, 8))
    for month, color in zip(range(1, 13), month_colors):
        line = plt.plot(
            grouped.index,
            grouped[month],
            label=MONTHS_OF_YEAR[month - 1],
            color=color,
        )[0]
        # Add label to the end of the line
        plt.text(
            grouped.index[-1] + 0.5,  # Position slightly to the right of the last point
            grouped[month].iloc[-1],  # Position at the last y-value
            MONTHS_OF_YEAR[month - 1],  # Label text
            color=color,
            fontsize="small",
            verticalalignment="center",
        )
            
    plt.xlabel("Hour of Day")
    plt.ylabel("Capacity Factor")
    plt.title("Hourly Mean Capacity Factor by Month")
    plt.legend(
        title="Month", bbox_to_anchor=(1.05, 1), loc="upper left", ncol=1, fontsize="small"
    )
    plt.tight_layout()
    plt.savefig("hourly_by_month_color.png")
    plt.close()

if __name__ == '__main__':
    open_sites()