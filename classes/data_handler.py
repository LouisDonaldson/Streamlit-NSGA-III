import json as json
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os
import streamlit as st

class DataHandler:
    def __init__(self):
        self.BeginImport()
        return
    
    def BeginImport(self):
        self.turbine_distance_matrix = self.load_distance_matrix()
        self.buoy_data = self.load_buoy_data()
        self.power_curve = self.load_turbine_power_curve()
        self.distance_from_port = self.load_distance_from_port()
        self.mast_df = self.load_mast_data()

        self.wind_by_day = {
            day: df["ANx_80_WS_Avg"].to_numpy()
            for day, df in self.mast_df.groupby("Days")
        }

        # Precompute power for wind speeds 0.0 → 25.0 in 0.1 m/s increments
        self.wind_lookup = np.zeros(251)

        for i in range(251):
            w = i / 10.0
            self.wind_lookup[i] = self.PowerFromWindScalar(w)



        return

    def load_distance_matrix(self, _json = json):
        print(os.getcwd())

        f = open("data/DistanceMatrix.json")
        turbine_distance_matrix = json.loads(f.read())
        return turbine_distance_matrix
    
    def load_buoy_data(self, _json = json):
        # f = open('data/buoy.json')
        f = open('data/daily_averages.json')

        buoy_data = json.loads(f.read())
        return buoy_data
    
    def load_turbine_power_curve(self):
        # Power curve of energy produced from turbine
        f = open('data/teeside_turbine_power_curve.csv')
        data = f.read()
        split = data.splitlines()
        power_curve = {}
        for x in range(2, len(split)):
            curve_split = split[x].split(",")
            #print(curve_split)
            #set = {curve_split[0] : curve_split[1]}
            power_curve[curve_split[0]] = curve_split[1]
        
        return power_curve
    
    def load_distance_from_port(self):
        # Distance from port data
        f = open('data/turbine_distance_from_port.csv')
        data = f.read()
        split = data.splitlines()

        distances = split[1].split(",")

        distance_from_port = []

        for x in distances:
            if(x == "Port"):
                continue
            else:
                distance_from_port.append(x) 
        
        return distance_from_port

    def load_mast_data(self):
        mast_df = pd.read_csv("data/mast_hourly_avg.csv")
        # mast_df["AN1_50S_WS_Avg"]
        return mast_df
    
    def filter_daily_mast(self, mast_df):
        daily_data = {
            day: df for day, df in mast_df.groupby(mast_df.index.date)
        }
        return daily_data

    def load_and_resample_to_hourly(self, csv_path):
        # Load CSV
        df = pd.read_csv(csv_path)

        # Parse timestamp column
        df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'])

        # Set timestamp as index
        df = df.set_index('TIMESTAMP')

        # Convert all columns to numeric (ignore errors)
        df = df.apply(pd.to_numeric, errors='coerce')

        # Resample to hourly using mean
        hourly_df = df.resample('1H').mean()

        return hourly_df

    def FindPowerGenerated(self, episode, hours=24):
        """
        Fast version: uses precomputed NumPy arrays instead of pandas slicing.
        Returns total power for the given episode (day).
        """

        # Get the pre-cached wind speeds for this day
        wind_speeds = self.wind_by_day[episode + 2]   # NumPy array, length 24

        # Convert wind speeds to power using vectorised operations
        total = 0.0
        for ws in wind_speeds:
            total += self.PowerFromWind(ws)
        
        # Sum the day's power
        return total


        # Sum the day's power
        return power_curve.sum()

    def FindPowerInMaintenanceWindow(self, episode, current_step, time_skipped=3):
        # Map step to hour index
        step_to_hour = {0: 9, 3: 12, 6: 15}
        start_hour = step_to_hour[current_step]
        end_hour = start_hour + time_skipped

        # Use your precomputed NumPy array
        winds = self.wind_by_day[episode + 2][start_hour:end_hour]

        total = 0.0
        for w in winds:
            total += self.PowerFromWind(w)

        return total

    def PowerFromWindScalar(self, wind):
        """
        Returns instantaneous turbine power (kW) for a given wind speed.
        Uses:
        - Cut-in / cut-out logic
        - Nearest 0.5 m/s rounding
        - Linear interpolation between power curve points
        """

        # Cut-in / cut-out
        if wind < 3.5 or wind > 25.0:
            return 0.0

        # Round to nearest 0.5 m/s
        wind_rounded = round(wind * 2) / 2

        # If exact match exists in the power curve
        if str(wind_rounded) in self.power_curve:
            return float(self.power_curve[str(wind_rounded)])

        # Otherwise interpolate between nearest 0.5 m/s points
        lower = round((wind_rounded - 0.5) * 2) / 2
        upper = round((wind_rounded + 0.5) * 2) / 2

        # Safety: ensure keys exist
        if str(lower) not in self.power_curve or str(upper) not in self.power_curve:
            return 0.0

        p_low = float(self.power_curve[str(lower)])
        p_high = float(self.power_curve[str(upper)])

        # Fractional distance between lower and upper
        frac = (wind - lower) / (upper - lower)

        # Linear interpolation
        return p_low + frac * (p_high - p_low)

    def PowerFromWind(self, wind):
        if wind < 0.0:
            return 0.0
        if wind > 25.0:
            return 0.0

        # Convert wind speed to index (0.1 m/s resolution)
        idx = int(wind * 10)

        return self.wind_lookup[idx]
    
    def CalculateCostOfFuel(self, wave_height, distance_travelled):
        cost_of_fuel = 180.7 # cost of fuel in £ per hour
        knot_speed = 0
        if(wave_height < 0.5):
            knot_speed = 25
        elif(wave_height < 1):
            knot_speed = 20
        elif(wave_height < 1.5):
            knot_speed = 15
        else:
            knot_speed = 5

        speed = knot_speed * 1852 # m/hr
        cost_per_meter = cost_of_fuel / speed
        overall_cost = cost_per_meter * distance_travelled
        return overall_cost

