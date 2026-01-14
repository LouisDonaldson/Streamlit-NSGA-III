import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import random
from datetime import datetime
import streamlit as st


from classes.turbine_model import Turbine, Component, Farm 

class Environment:
    def __init__(self, step_limit, days_limit, data_handler, _start_day, _stream=None):
        self.start_day = _start_day
        self.stream = _stream
        self.data_handler = data_handler
        self.num_turbines = 27 #  this can go up to 27 turbines (Teeside farm layout)
        self.state_size = self.num_turbines + 1 # 27 turbines # 1 start location (port) [location][timestep]
        self.action_size = 1 + self.num_turbines * 6 # 0- Go back to port 1- do nothing [move to location]
        # print(self.action_size)
                             # 2- perform maintenance on specific turbine (Turbine 1 = [2])
        self.turbine_distance_matrix =  self.data_handler.turbine_distance_matrix
        self.buoy_data =  self.data_handler.buoy_data
        self.distance_from_port =  self.data_handler.distance_from_port
        self.current_state = 0

        self.step_limit = step_limit
        self.step_interval = int(step_limit/3)
        self.days_limit = days_limit

        # Shows each turbine's health
        
        self.current_distance_travelled = 0
        self.turbine_health_decrease_list = [0] * 500
        turbine_decay_rate = 0.01

        self.levelised_cost_of_electricity = 70

        for x in range(len(self.turbine_health_decrease_list)):
            self.turbine_health_decrease_list[x] = (np.exp(-turbine_decay_rate*x)) * 100

        self.turbine_health = [self.turbine_health_decrease_list[0]] * self.num_turbines

        self.turbine_health_threshhold = 25

        self.turbines = Farm(self.num_turbines, self.turbine_health_decrease_list)
        self.csv = ""

        self.power_difference = [] # power difference in £/mWh
        self.cost = [] # distance
        self.power_generated = [] # power generated in mWh

        self.wave_height_violations = []

        self.episode_power_gained = 0
        self.episode_power_gained_new = 0

        self.episode_distance_travelled = 0
        self.episode_distance_travelled_new = 0 

        self.episode_health_increase = 0

        self.iteration_power_gained = []
        self.iteration_power_gained_new = []

        self.iteration_distance_travelled = []
        self.iteration_distance_travelled_new = []

        self.iteration_health_increase = []
        
    def reset(self):

        self.current_state = 0
        #self.turbine_health = [100] * self.num_turbines
        self.current_distance_travelled = 0
        #self.turbine_health = [self.turbine_health_decrease_list[0]] * self.num_turbines
        return self.current_state

    def hard_reset(self):
        self.current_state = 0
        self.turbine_health = [self.turbine_health_decrease_list[0]] * self.num_turbines
        self.current_distance_travelled = 0
        
        return self.current_state

    def decay_turbine_health(self, lb=1, ub=3):
        """
        Randomly degrade each turbine's health by moving down the
        turbine_health_decrease_list by 1–3 steps.
        """

        for turbine in self.turbines.turbines:  # or self.env.turbines.turbines depending on your structure
            degrade_steps = round(random.uniform(lb, ub))

            current_health = turbine.overall_health

            # Find the index of the current health in the decay list
            try:
                idx = self.turbine_health_decrease_list.index(current_health)
            except ValueError:
                # If the exact value isn't in the list, find the closest lower value
                # This keeps the system stable even if health was modified elsewhere
                idx = max(
                    i for i, v in enumerate(self.turbine_health_decrease_list)
                    if v >= current_health
                )

            # Compute the new index after degradation
            new_idx = idx + degrade_steps

            # Clamp to the end of the list
            if new_idx >= len(self.turbine_health_decrease_list):
                new_idx = len(self.turbine_health_decrease_list) - 1

            # Assign the new health value
            turbine.overall_health = self.turbine_health_decrease_list[new_idx]
   
    def increase_turbine_health(self, maintenance_details = {}):
        turbine_health_increase = round(random.uniform(50, 100))
        
        # print(turbine_index)
        initial_health = self.turbines.turbines[maintenance_details["turbine_id"] - 1].overall_health
        self.turbines.repair_component(maintenance_details["turbine_id"] - 1, maintenance_details["component"], turbine_health_increase) # -1 for 0 index
        health_increase_amount = self.turbines.turbines[maintenance_details["turbine_id"] - 1].overall_health - initial_health
        type = "corrective" if initial_health < self.turbine_health_threshhold else "preventative"

        return health_increase_amount, type
    
    def interpret_component(self, component_id):
        if component_id == 1:
            return "nacelle"
        elif component_id == 2:
            return "blades"
        elif component_id == 3:
            return "tower"
        elif component_id == 4:
            return "generator"
        elif component_id == 5:
            return "gearbox"
        elif component_id == 6:
            return "control_system"
        else:
            raise Exception("Invalid component ID")
        
    def interpret_action(self, action):
        return_to_port = False
        do_nothing = False
        perform_maintenance = False
        maintenance_action = {"return_to_port": return_to_port, 
                              "do_nothing": do_nothing, 
                              "perform_maintenance": perform_maintenance,
                              "maintenance_details": None}
        if action == 0:
            maintenance_action["return_to_port"] = True
            # return "Return to port"
        elif action == 1:
            maintenance_action["do_nothing"] = True
            # return "Do nothing"
        else:
            components_per_turbine = 6
            total_turbines = self.num_turbines
            max_action = 2 + components_per_turbine * total_turbines

            if action < 1 or action > max_action:
                raise Exception("Invalid action: out of bounds")

            # Offset from first repair action
            maintenance_action["perform_maintenance"] = True
            offset = action - 2
            turbine_id = offset // components_per_turbine + 1
            component_id = offset % components_per_turbine + 1
            component = self.interpret_component(component_id)
            maintenance_action["maintenance_details"] = {"turbine_id": turbine_id, "component": component}

        return maintenance_action
        
    def step(self, action, current_step, env, episode):
        #print(self.get_turbine_health_cumulative())

        intepreted_action = self.interpret_action(action)
        # maintenance_action = self.interpret_action(0)

        current_state = self.current_state
        done = False
        hours_skipped = 0
        overworked = False
        reward = 0
        health_increase = 0
        type = None
        maintenance_type = ""

        self.decay_turbine_health()
        
        if(intepreted_action["do_nothing"] == False and intepreted_action["return_to_port"] == False):
            # moving to a new turbine to perform maintenance
            new_state = (intepreted_action["maintenance_details"]["turbine_id"] -1) # -1 for 0 index
            health_increase, type = self.increase_turbine_health(intepreted_action["maintenance_details"])
            self.episode_health_increase += health_increase
            step_health_increase = health_increase
            maintenance_type = type

            if(current_state == 0):
                self.current_distance_travelled += float(self.distance_from_port[new_state]) * 1000 # distance in meters
            else:
                distance_from_next_turbine = float(self.turbine_distance_matrix[current_state][action - 2]) # current_state is correct turbine location due to 0 index
                self.current_distance_travelled += distance_from_next_turbine
                
                # reward += 100 - self.turbine_health[new_state]

            if(current_step < (self.step_limit - 3)):
                hours_skipped = self.step_interval
            else:
                overworked = True
        elif(intepreted_action["return_to_port"] and current_state == 0):
            # going back to port
            new_state = 0
            distance_travelled = 0
            self.current_distance_travelled += distance_travelled
            done = True  
        elif(intepreted_action["return_to_port"] and current_state != 0):
            # going back to port
            new_state = 0
            distance_travelled = float(self.distance_from_port[current_state])
            self.current_distance_travelled += distance_travelled
            done = True

            # if(current_step == self.step_limit):
                # overworked = True
            
        elif(intepreted_action["do_nothing"]):
            # doing nothing            
            new_state = current_state
            if(current_step < (self.step_limit - 3)):
                hours_skipped = self.step_interval
            if(current_step == self.step_limit):
                overworked = True

        # if next move is the step limit and is not going back to port, then the agent is overworked
        turbine_maintained = None
        
        ## turbine has been maintained. 
        ## find power lost due to downtime
        power_lost = 0
        if(intepreted_action["do_nothing"] == False and intepreted_action["return_to_port"] == False):
            turbine_maintained = intepreted_action["maintenance_details"]["turbine_id"] - 1 # -1 for 0 index
            _percentage_degradation = self.turbine_health[turbine_maintained] / 100
            power_lost = (self.data_handler.FindPowerInMaintenanceWindow(episode, current_step, hours_skipped)) * _percentage_degradation

         
        reward += self.calculate_reward(maintenance_type, health_increase, self.current_distance_travelled, intepreted_action, hours_skipped, current_step, env, episode)
        
        # st.write(intepreted_action)
        if(float(self.get_average_hs_at_episode(self.buoy_data, episode)) > 1.5 and intepreted_action['perform_maintenance']):
            wave_height = self.get_average_hs_at_episode(self.buoy_data, episode)
            env.wave_height_violations.append(wave_height - 1.5)
            # reward = -reward



        if(overworked == True):
            done = True
            # reward = -reward

        
        # If any turbine health is below threshold, punish!
        # for x in self.turbine_health:
        #     if(x < self.turbine_health_threshhold):
        #         reward -= 10

        return new_state, reward, done, hours_skipped, type, power_lost
        
    def get_random_action(self, current_state):
        self.current_state = current_state
        if(current_state == 0):
            # only able to do nothing or perform maintenance on another turbine [1]...[29] but not [0]
            random_action = round(random.uniform(1, self.action_size - 1))
            return random_action
        elif(current_state > 0):
            return round(random.uniform(0, self.action_size - 1))

    def get_turbine_health_average(self):
        cumulative = 0
        for _x in self.turbine_health:
            cumulative += _x
        #print(cumulative)
    
        cumulative = cumulative / len(self.turbine_health)

    
        ##cumulative = cumulative / len(self.turbine_health)
        return cumulative
    
    def get_average_hs_at_episode(self, data, day_number):
        offset = self.start_day + day_number
        
        if offset >= len(data):
            offset = offset - len(data)

        return data[offset]["Hs"]
    

    def calculate_reward(self, maintenance_type, health_increase, distance_travelled, action, time_skipped, current_step, env, episode):
        # reward is calculated based on the cumulative turbine health / the distance travelled

        reward = 0

        power_lost = 0
        power_gained = 0

        # cost calculated here in £
        ####################
        cost = self.data_handler.CalculateCostOfFuel(float(self.get_average_hs_at_episode(self.buoy_data, episode)), distance_travelled)

        if(action["perform_maintenance"]):
            turbine = [_turbine for _turbine in self.turbines.turbines if _turbine.num + 1 == action["maintenance_details"]["turbine_id"]]
            bounds = turbine[0].components[action["maintenance_details"]["component"]].repair_cost[maintenance_type]
            action_cost = round(random.uniform(bounds['lb'], bounds['ub']))
            cost += action_cost
            if(action_cost == 0):
                raise Exception("Action cost should not be 0...")

        ####################

        # reward weightings
        alpha = 1.5 # power gained # positive
        beta = 1 # power lost # negative
        gamma = 1.5 # cost # negative
        delta = 1 # health increase # positive

        if action["perform_maintenance"] and cost == 0:
            raise EnvironmentError("Something is not right here")

        ## ["out"] to NSGA
        env.reward["Cost"] += cost

        reward = (alpha * power_gained) - (beta * power_lost) - (gamma * cost) + (delta * health_increase)
        #reward = (alpha * power_gained) - (gamma * cost)

        
        return reward 
    # calculate reward based on the amount of energy that the turbine will have not made based on the weather data.

    # def get_suggested_action(self, current_step):
    #     lowest_health_turbine = self.turbine_health.index(min(self.turbine_health))
    #     #print(lowest_health_turbine)
    #     # [turbine index + 1] = action
    #     suggested_action = lowest_health_turbine + 1
    #     new_state, reward, done, hours_skipped, type = self.step(suggested_action, current_step)
    #     return suggested_action, reward
