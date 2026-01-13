import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)


class EnvironmentHandler:
    def __init__(self, schedule_to_simulate, data_handler, Environment, number_of_days, _start_day, _stream=None):  # Constructor
        self.schedule = np.round(schedule_to_simulate).astype(int)
        self.number_of_days = number_of_days
        self.stream = _stream

        self.schedule = self.FormatSchedule(self.schedule)

        days = number_of_days
        hours = 5

        self.encoded_schedule = self.schedule
        self.env = Environment(days, hours, data_handler, _stream = _stream, _start_day = _start_day)
        self.day = 0
        self.time = 0
        self.action_string = ""

        self.current_ep = 0

        self.csv= "Counter, Ep, Step, States, Actions, Cost, Power Generated, Overall \n"

        self.reward = {"Cost": 0.0, "Power_Generated": 0.0, "Overall": 0.0  }
        self.wave_height_violations = []
        #self.GetAction(0)
        
        return
    
    def FormatSchedule(self, schedule):
        return schedule.reshape(-1, 3)
 
    def GetAction(self, current_state, episode):
        #print(self.day)
        #print(self.time)

        next_action = 0

        if(self.current_ep != episode):
            self.time = 0
            self.current_ep = episode
            next_action = self.schedule[episode][self.time]
        else:
            if(self.time > len( self.schedule[episode]) - 1):
                next_action = 0
            else:
                next_action = self.schedule[episode][self.time]

        self.time = self.time + 1
        
        
        return next_action
 
    def RunSim(self, episodes=7, steps = 5, verbose = False):
        counter = 1

        if(verbose):
            print("Starting simulation...")
                 
        for episode in range(episodes):
            if(verbose):
                print(f"Day: {episode + 1}\n")
            # reset the environment
            state = self.env.reset()
            done = False
            cum_reward = 0

            if(verbose):
                print(f"Initial state: {state}")

            episodes_states = "0-"
            episodes_actions = ""
            current_s = 0

            for s in range(0, steps):

                action = self.GetAction(int(state), episode)
                #print(f"Action: {action}, Step: {current_s}")
                # print(f"Chosen action: {action}")
                
                new_state, reward, done, hours_skipped, type = self.env.step(action, current_s, self, episode, )

                self.reward["Overall"] = self.reward["Overall"] + reward

                cum_reward += reward

                state = int(new_state)

                episodes_states += f"{state}-"
                episodes_actions += f"{action}({type})-"

                step_it = counter

                if(verbose):
                    print(f"New state: {state}. Action taken: {action}. \nReward: {reward}. Cum reward: {cum_reward}. \nHours skipped: {hours_skipped}. Done: {done}\n\n")

                if verbose:
                    print(self.reward["Cost"])

                # If return to port is the new state, skip the rest of the actions in the queue for the day
                if(state == 0 and action == 0):
                    break

                # if done, finish episode
                if done == True:
                    break

                if(current_s + hours_skipped >= steps):
                    break
                else:
                    s += hours_skipped
                    current_s = current_s + hours_skipped
                
                
            counter += 1

            self.csv += f"{counter}, {episode}, {s}, {episodes_states}, {episodes_actions}, {(self.reward["Cost"])}, {self.reward["Power_Generated"]}, {(self.reward["Overall"])} \n"
            #print(counter)

        # if(self.reward['Cost'] == 0):
        #     print()
        #     raise EnvironmentError("Cost was")

        
        self.env.hard_reset()
        if(verbose):
            print(f"Episode reward: {cum_reward}\n")
        return self.env    
            # print(f"Distance travelled: {env.episode_distance_travelled}.\nPower gained: {env.episode_power_gained}.\nHealth increase from maintenance: {env.episode_health_increase}\n")
         
