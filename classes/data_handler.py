import json as json
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os

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
        return

    def load_distance_matrix(self, _json = json):
        print(os.getcwd())

        f = open("C:/Users/lj200/OneDrive/Documents/GitHub/GA-Practice/Code/data/DistanceMatrix.json")
        turbine_distance_matrix = json.loads(f.read())
        return turbine_distance_matrix
    
    def load_buoy_data(self, _json = json):
        f = open('C:/Users/lj200/OneDrive/Documents/GitHub/GA-Practice/Code/data/buoy.json')
        buoy_data = json.loads(f.read())
        return buoy_data
    
    def load_turbine_power_curve(self):
        # Power curve of energy produced from turbine
        f = open('C:/Users/lj200/OneDrive/Documents/GitHub/GA-Practice/Code/data/teeside_turbine_power_curve.csv')
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
        f = open('C:/Users/lj200/OneDrive/Documents/GitHub/GA-Practice/Code/data/turbine_distance_from_port.csv')
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
        mast_df = pd.read_csv("C:/Users/lj200/OneDrive/Documents/GitHub/GA-Practice/Code/data/new_mast.csv")
        # mast_df["AN1_50S_WS_Avg"]

        return mast_df

    def FindPowerGenerated(self, step, time): # calculates power generated in kW/H
        if(time == 0):
            time = 1
            
        average_wind = self.mast_df["AN1_50S_WS_Avg"][step] # this needs changing in the future

        average_wind = round(average_wind*2)/2
        power_gen = self.power_curve[str(average_wind)]
        
        return (int(power_gen) * time)


        power_generated = FindPowerGenerated(1, 2) # step (day, number of hours)
        print(power_generated)
        # for testing purposes. [0]-[6] will be used of the wind data

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

    