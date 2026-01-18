import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)


class EnvironmentHandler:
    def __init__(self, schedule_to_simulate, data_handler, Environment, number_of_days, _start_day, _stream=None):  # Constructor
        self.schedule = np.round(schedule_to_simulate).astype(int)
        self.number_of_days = number_of_days
        self.stream = _stream

        self.schedule = self.FormatSchedule(self.schedule)

        self.days = number_of_days
        hours = 9

        self.encoded_schedule = self.schedule
        self.env = Environment(hours, self.days, data_handler, _stream = _stream, _start_day = _start_day)
        self.day = 0
        self.time = 0
        self.action_string = ""

        self.current_ep = 0

        self.csv= "Counter, Ep, Step, States, Actions, Cost, Power Generated, Overall \n"

        self.reward = {"Cost": 0.0, "Power_Generated": 0.0, "new_Power_Generated": 0.0, "Overall": 0.0  }
        self.wave_height_violations = []
        self.hours_performing_maintenance = 0
        self.episode_snapshots = []
        self.turbine_health_snapshots = []
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
    
    # def FindDayPowerGenerated(self, episode, maintenance_hours, turbines_under_maintenance=1):
    #     """
    #     Computes total farm energy for one day (kWh).
    #     - Uses hourly wind data for the correct day (via Days column)
    #     - Subtracts maintenance losses per turbine
    #     - Applies average turbine health scaling
    #     """

    #     num_turbines = len(self.env.turbines.turbines)

    #     # 1. Compute average turbine health
    #     avg_health = sum(t.overall_health for t in self.env.turbines.turbines)
    #     avg_health = (avg_health / num_turbines) / 100.0

    #     # 2. Extract the 24 hourly rows for this episode/day
    #     mast_df = self.env.data_handler.mast_df
    #     day_df = mast_df[mast_df["Days"] == episode + 2] # offset by 2 because Day 1 only has 1 row

    #     if len(day_df) != 24:
    #         raise ValueError(f"Day {episode} does not contain 24 hourly rows. Found {len(day_df)} rows.")

    #     # 3. Compute energy for one turbine over this day
    #     single_turbine_energy = 0.0
    #     for wind in day_df["ANx_80_WS_Avg"].values:
    #         single_turbine_energy += self.env.data_handler.PowerFromWind(wind)

    #     # 4. Farm energy before maintenance
    #     farm_energy_before = single_turbine_energy * num_turbines

    #     # 5. Maintenance loss (per turbine offline)
    #     hourly_power = single_turbine_energy / 24
    #     maintenance_loss = hourly_power * maintenance_hours * turbines_under_maintenance

    #     # 6. Final farm energy
    #     farm_energy_after = farm_energy_before - maintenance_loss

    #     # 7. Apply health scaling
    #     farm_energy_after *= avg_health

    #     # Debug prints
    #     print(f"\nEpisode: {episode}")
    #     print(f"Single turbine: {single_turbine_energy/1000:.3f} MWh")
    #     print(f"Farm before maintenance: {farm_energy_before/1000:.3f} MWh")
    #     print(f"Maintenance loss: {maintenance_loss/1000:.3f} MWh")
    #     print(f"Farm after maintenance: {farm_energy_after/1000:.3f} MWh")
    #     print(f"Avg health scaling: {avg_health:.2f}")

    #     return farm_energy_after  # kWh
 
    def RunSim(self, verbose = False):
        counter = 1

        power_gen_so_far = 0
        power_lost_so_far = 0

        turbine_power_gen_overall_snapshot = []

        if(verbose):
            print("Starting simulation...")


        for episode in range(self.days):
            # print(f"Episode: {episode + 1}")
            # for t in self.env.turbines.turbines:
            #     print(t.overall_health)
            # print()

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

            episode_hours_skipped = 0

            day_power_lost = 0 # Power lost due to turbine downtime

            turbine_ep_power_gen = np.zeros(len(self.env.turbines.turbines))
            # arr = 

            for s in range(0, self.env.step_limit):
                action = self.GetAction(int(state), episode)
                #print(f"Action: {action}, Step: {current_s}")
                # print(f"Chosen action: {action}")
                
                new_state, reward, done, hours_skipped, type, power_lost = self.env.step(action, current_s, self, episode, )
                day_power_lost += power_lost

                self.reward["Overall"] = self.reward["Overall"] + reward
                self.hours_performing_maintenance += hours_skipped # Overall hours skipped 
                episode_hours_skipped += hours_skipped # Episode (day) hours skipped

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

                if(current_s + hours_skipped >= self.env.step_limit):
                    break
                else:
                    s += hours_skipped
                    current_s = current_s + hours_skipped
                    
            counter += 1

            self.csv += f"{counter}, {episode}, {s}, {episodes_states}, {episodes_actions}, {(self.reward["Cost"])}, {self.reward["Power_Generated"]}, {(self.reward["Overall"])} \n"
            
            farm_wide_power_generated = 0
            turbines_health = []
            
            for i, t in enumerate(self.env.turbines.turbines):
                raw_health = t.overall_health / 100
                t_health = 0.8 + 0.2 * raw_health

                 # / 100 to convert to scalar. 100% health = 1
                turbines_health.append(t.overall_health)
                possible_power_production = self.env.data_handler.FindPowerGenerated(episode, day_offset = self.env.start_day)
                
                # print(f"T{i+1} | Possible power: {possible_power_production} | Turbine Health: {t_health*100}% | Actual power: {possible_power_production * t_health}")
                
                farm_wide_power_generated += (possible_power_production * t_health)
                turbine_ep_power_gen[i] = possible_power_production * t_health

            # print("---------------")
            # print(f"Farm wide production: {farm_wide_power_generated} KWh ({farm_wide_power_generated / 1000} MWh) | Power lost: {day_power_lost} KWh")

            # turbine_power_gen_overall_snapshot.append(turbine_ep_power_gen)

            self.episode_snapshots.append({
                "day": episode + 1,
                "t_health": turbines_health,
                "generated_power": farm_wide_power_generated - day_power_lost,
                "potential_generated_power": farm_wide_power_generated,
                "power_lost": day_power_lost,
                "cost": self.reward["Cost"],
                "t_power": turbine_ep_power_gen
            })
            # farm_wide_power_generated = single_turbine_power_generated * len(self.env.turbines.turbines)

            power_gen_so_far += farm_wide_power_generated - day_power_lost
            power_lost_so_far += day_power_lost
            
            print()

        self.reward['new_Power_Generated'] += power_gen_so_far
        # print(f"Overall power generated: {power_gen_so_far} KWh ({power_gen_so_far / 1000} MWh) | Power lost: {power_lost_so_far} KWh ({power_lost_so_far / 1000} MWh)")

        if(verbose):
            print(f"Episode reward: {cum_reward}\n")

        return self.env    
            # print(f"Distance travelled: {env.episode_distance_travelled}.\nPower gained: {env.episode_power_gained}.\nHealth increase from maintenance: {env.episode_health_increase}\n")
         
