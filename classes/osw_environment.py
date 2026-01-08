import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

from classes.turbine_model import Turbine, Component, Farm 

class Environment:
    def __init__(self, step_limit, days_limit, data_handler):
        self.data_handler = data_handler
        self.num_turbines = 27 #  this can go up to 27 turbines (Teeside farm layout)
        self.state_size = self.num_turbines + 1 # 27 turbines # 1 start location (port) [location][timestep]
        self.action_size = 2 + self.num_turbines # 0- Go back to port 1- do nothing [move to location]
                             # 2- perform maintenance on specific turbine (Turbine 1 = [2])
        self.turbine_distance_matrix =  self.data_handler.turbine_distance_matrix
        self.buoy_data =  self.data_handler.buoy_data
        self.distance_from_port =  self.data_handler.distance_from_port
        self.current_state = 0

        self.step_limit = step_limit
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

        # self.turbines = Farm(self.num_turbines)

        self.csv = ""

        #print( self.turbine_health_decrease_list)

        # print(f"Number of turbines: {self.num_turbines}\n")
        # print(f"State size: {self.state_size}\n")
        # print(f"Action size: {self.action_size}\n")
        # print(f"Distance matrix loaded\n")
        # print(f"Distance from port data loaded\n")
        # print(f"Weather Data loaded\n")

        self.power_difference = [] # power difference in £/mWh
        self.cost = [] # distance
        self.power_generated = [] # power generated in mWh

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


    def decay_turbine_health(self):
        # Randomly decay the turbine 1 - 3
        
        #print(increase)
        for x in range(0,self.num_turbines):
            increase = round(random.uniform(1, 3))
            try:
                self.turbine_health[x] = self.turbine_health_decrease_list[self.turbine_health_decrease_list.index(self.turbine_health[x]) + increase]
            except:
                self.turbine_health[x] = self.turbine_health_decrease_list[len(self.turbine_health_decrease_list) - 1]
     
    def increase_turbine_health(self, turbine_index):
        turbine_health_increase = 50
        
        # print(turbine_index)

        health_current_state = self.turbine_health[turbine_index]

        # determines whether or not maintenance is corrective of preventative
        if (health_current_state < self.turbine_health_threshhold):
            type = "Corrective"
        else:
            type = "Preventative"

        health_decrease_index = self.turbine_health_decrease_list.index(health_current_state)
        if(type == "Corrective"):
            new_health = self.turbine_health_decrease_list[0]
        else:
            if(health_decrease_index - turbine_health_increase < 0):
                new_health = self.turbine_health_decrease_list[0]
            else:
                new_health = self.turbine_health_decrease_list[health_decrease_index - turbine_health_increase]

        health_increase_amount = new_health - health_current_state

        #print(new_health)
        #raise EnvironmentError("Pause")
        
        self.turbine_health[turbine_index] = new_health

        return health_increase_amount, type
    
    def step(self, action, current_step, env):
        #print(self.get_turbine_health_cumulative())

        
        current_state = self.current_state
        done = False
        hours_skipped = 0
        overworked = False
        reward = 0
        health_increase = 0
        type = None
        
        if(action >= 2):
            # moving to a new turbine to perform maintenance
            new_state = action - 2
            health_increase, type = self.increase_turbine_health(new_state)
            self.episode_health_increase += health_increase

            if(current_state == 0):
                self.current_distance_travelled += float(self.distance_from_port[new_state]) * 1000 # distance in meters
            else:
                distance_from_next_turbine = float(self.turbine_distance_matrix[current_state][action - 2]) # current_state is correct turbine location due to 0 index
                self.current_distance_travelled += distance_from_next_turbine
                
                # reward += 100 - self.turbine_health[new_state]

            if(current_step < (self.step_limit - 3)):
                hours_skipped = 2
            else:
                overworked = True
        elif(action == 0 and current_state == 0):
            # going back to port
            new_state = 0
            distance_travelled = 0
            self.current_distance_travelled += distance_travelled
            done = True  
        elif(action == 0):
            # going back to port
            new_state = 0
            distance_travelled = float(self.distance_from_port[current_state])
            self.current_distance_travelled += distance_travelled
            done = True

            # if(current_step == self.step_limit):
                # overworked = True
            
        elif(action == 1):
            # doing nothing
            new_state = current_state
            if(current_step == self.step_limit):
                overworked = True

        # if next move is the step limit and is not going back to port, then the agent is overworked
       
         
        reward += self.calculate_reward(self.get_turbine_health_average(), health_increase, self.current_distance_travelled, action, hours_skipped, current_step, env)
    
        if(overworked == True):
            done = True
            reward = -reward

        
        # If any turbine health is below threshold, punish!
        # for x in self.turbine_health:
        #     if(x < self.turbine_health_threshhold):
        #         reward -= 10

        return new_state, reward, done, hours_skipped, type
        
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

    def calculate_reward(self, average_turbine_health, health_increase, distance_travelled, action, time_skipped, current_step, env):
        # reward is calculated based on the cumulative turbine health / the distance travelled

        reward = 0

        power_lost = 0
        power_gained = 0

        turbine_maintained = None
        
        if(action >= 2):
            turbine_maintained = action - 2
            _percentage_degradation = self.turbine_health[turbine_maintained] / 100
            power_lost = (self.data_handler.FindPowerGenerated(current_step, time_skipped)) * _percentage_degradation
        
        #((FindPowerGenerated(current_step, time_skipped)) * self.num_turbines * (average_turbine_health / 100))
        
        
        for x in range(0, self.num_turbines):
            if(x == turbine_maintained):
                continue
            turbine_power_generated = self.data_handler.FindPowerGenerated(current_step, time_skipped)
            percentage_degradation = self.turbine_health[x] / 100
            power_gained += turbine_power_generated * percentage_degradation


        power_difference = power_gained - power_lost # power difference calculated in kW/h        

        power_difference = power_difference / 1000 # convert to MWh
        power_difference = power_difference * self.levelised_cost_of_electricity # convert to £

        self.power_difference.append(power_difference)
        self.power_generated.append(power_gained)
        self.cost.append(distance_travelled)

        cost = self.data_handler.CalculateCostOfFuel(float(self.buoy_data[current_step]["Hs"]), distance_travelled)

        self.episode_power_gained += power_gained
        self.episode_distance_travelled += cost
        self.episode_power_gained_new += power_gained
        self.episode_distance_travelled_new += cost

        # reward weightings
        alpha = 1.5 # power gained # positive
        beta = 1 # power lost # negative
        gamma = 1.5 # cost # negative
        delta = 1 # health increase # positive

        env.reward["Cost"] += gamma * cost
        env.reward["Power_Generated"] += alpha * power_gained

        reward = (alpha * power_gained) - (beta * power_lost) - (gamma * cost) + (delta * health_increase)
        #reward = (alpha * power_gained) - (gamma * cost)

        if(float(self.buoy_data[current_step]["Hs"]) > 1.5):
            reward = -reward

        return reward 
    # calculate reward based on the amount of energy that the turbine will have not made based on the weather data.

    def get_suggested_action(self, current_step):
        lowest_health_turbine = self.turbine_health.index(min(self.turbine_health))
        #print(lowest_health_turbine)
        # [turbine index + 1] = action
        suggested_action = lowest_health_turbine + 1
        new_state, reward, done, hours_skipped, type = self.step(suggested_action, current_step)
        return suggested_action, reward
