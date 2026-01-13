import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from pymoo.indicators.hv import HV
import pandas as pd
import altair as alt
import xgboost as xgb
import shap as shap
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

from classes.nsga_iii import NSGAIII_Interface

if "running" not in st.session_state:
    st.session_state.running = False

if "show_parameters" not in st.session_state:
    st.session_state.show_parameters = True
   
if "run" not in st.session_state:
    st.session_state.run = False

if "simulation_finished" not in st.session_state:
    st.session_state.simulation_finished = False

if "create_data_stream" not in st.session_state:
    st.session_state.create_data_stream = True 

plt.style.use("default")

altair_style = {
    "figure.figsize": (10, 6),
    "axes.facecolor": "white",
    "axes.edgecolor": "#E0E0E0",
    "axes.linewidth": 1,
    "axes.grid": True,
    "grid.color": "#E6E6E6",
    "grid.linewidth": 1,
    "grid.alpha": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
    "font.size": 13,
    "axes.titlesize": 18,
    "axes.labelsize": 15,
    "xtick.color": "#555",
    "ytick.color": "#555",
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "legend.frameon": False,
    "scatter.marker": "o",
}

plt.rcParams.update(altair_style)

st.sidebar.number_input("Age")


class DataStream:
    def __init__(self):
        self.data = []
        self.new_data = False
    
    def AddData(self, message):
        self.data.append(message)
        self.new_data = True

    def GetData(self, final=False):
        if self.new_data:
            self.new_data = False
            return_data = self.data
            self.data = []
            return return_data
        return None

st.session_state.data_stream = DataStream()
def start_simulation(nsga_params, stream):
    nsga_interface = NSGAIII_Interface(nsga_params, _stream=stream, st=st)
    
    st.session_state.running = True

    sim_data = nsga_interface.run()

    st.session_state.running = False
    st.session_state.simulation_finished = True

    return sim_data


st.badge("Under Construction", color="red")
# Title
st.title("NSGA-III Offshore Wind Farm Scheduling Optimisation Simulation")
st.markdown("This application allows you to configure and run a simulation for optimising offshore wind farm scheduling for maintenance operations using the NSGA-III algorithm.")
st.markdown("For in-depth information on how to understand the graphs and the technical information relating to the models, please visit the link below.")
st.link_button("Further Information and Documentation", "https://mammoth-cough-70c.notion.site/OSW-NSGA-III-Environment-2-0-2df063e6bdf280dcb0e9f2410734c92a")


st.divider()

# Configuration box
# If simulation not started, show configuration box
if st.session_state.show_parameters == True:
    st.header("Simulation Configuration")

    # Input fields
    max_generations = st.number_input("Maximum Generations", min_value=1, value=10)
    population_size = st.number_input("Population Size", min_value=1, value=20)
    days = st.number_input("Days", min_value=1, value=7)

    # Pareto fronts with validation
    pareto_fronts = st.number_input("Pareto Fronts to Show", min_value=1, value=10)
    if pareto_fronts > max_generations:
        st.warning("Pareto fronts must be less than the number of generations.")

    params = {
        "generations": max_generations,
        "population_size": population_size,
        "days": days,
        "paretos_to_display": pareto_fronts
        }

    if st.button("Start Simulation"):
        ## parameters are valid
        # running simulation
        st.session_state.show_parameters = False
        st.session_state.run = True
        st.session_state.nsga_params = params
        st.rerun()


    st.divider()


if st.session_state.get("run", True):
    st.success("Simulation started.")
    st.session_state.simulation_finished = False

    st.session_state.run = False
    st.session_state.result = start_simulation(
        st.session_state.nsga_params,
        st.session_state.data_stream
    )
    
    st.session_state.simulation_finished = True
    st.rerun()

if(st.session_state.simulation_finished):
    # simulation finished. Show results below
    st.success("Simulation completed.")
    # results can be accessed through 'st.session_state.result'
    st.header("Results Visualization")

<<<<<<< Updated upstream
=======
    # access turbines
    #st.write(st.session_state.sim_envs[0].turbines.turbines)

    # Flip power generation back to positive
    true_power = -st.session_state.result.F[:, 1]

    # Sort indices by ascending power
    sorted_indices = np.argsort(true_power)

    # Get sorted schedules and objectives
    sorted_schedules = [st.session_state.result.X[i].reshape((st.session_state.nsga_params['days'], 3)) for i in sorted_indices]
    sorted_objectives = st.session_state.result.F[sorted_indices]
    sorted_environnments = st.session_state.result.opt.get("env")[sorted_indices]

    st.code(sorted_objectives[1][0])
    st.code(sorted_environnments[1].reward["Cost"])


    st.code(f"Number of Schedules found: {len(sorted_schedules)}")

    # st.session_state.sim_envs[0].reward["Cost"]
    # st.code(st.session_state.result.history[0].pop.get("F")[1][0])

    # schedule_environment_handler = st.session_state.sim_envs[-3:]
    # st.write((schedule_environment_handler[0].reward["Cost"]))
    # st.write((schedule_environment_handler[0].reward["Power_Generated"]))



>>>>>>> Stashed changes
    def Plot_Pareto_Final():
        #
        # Pareto Front of Final Population
        #
        plt.clf() 
<<<<<<< Updated upstream
        st.markdown("### Pareto Front of Final Population")
        # Flip power generation back to positive
        true_power = -st.session_state.result.F[:, 1]

        # Sort indices by ascending power
        sorted_indices = np.argsort(true_power)

        # Get sorted schedules and objectives
        sorted_schedules = [st.session_state.result.X[i].reshape((st.session_state.nsga_params['days'], 3)) for i in sorted_indices]
        sorted_objectives = st.session_state.result.F[sorted_indices]


=======
        
>>>>>>> Stashed changes
        # Visualize the Pareto front
        plt.figure(figsize=(10, 6))
        plt.scatter(sorted_objectives[:, 0], true_power[sorted_indices], c='blue', label="Pareto Front")

        # Annotate each point with its sorted index
        for i, idx in enumerate(sorted_indices):
            x = st.session_state.result.F[idx, 0]              # Cost
            y = -st.session_state.result.F[idx, 1]             # Power generation
            plt.text(x, y, str(i + 1), fontsize=10, ha='center', va='bottom')

        plt.xlabel("Cost")
        plt.ylabel("Power Generation")
        plt.title("Pareto Front with Sorted Indices")
        plt.grid(True)
        plt.legend()

        st.pyplot(plt)
        st.divider()

    def Plot_Pareto_Generations():
        #
        # Pareto Front of Generations
        #
        plt.clf() 
        st.markdown("### Pareto Front Evolution Across Generations")
        all_x = []
        all_y = []
        all_gen = []

        num_to_show = 5

        for gen, entry in enumerate(st.session_state.result.history):
            if(gen % (len(st.session_state.result.history) // num_to_show) != 0):
                continue
            F = entry.pop.get("F")
            for cost, power in F:
                all_x.append(cost)
                all_y.append(-power)  
                all_gen.append(gen)   

        all_x = np.array(all_x)
        all_y = np.array(all_y)
        all_gen = np.array(all_gen)

        plt.figure(figsize=(10, 6))
        sc = plt.scatter(all_x, all_y, c=all_gen, cmap='viridis', s=40,)

        cbar = plt.colorbar(sc)
        cbar.set_label('Generation Index')

        plt.xlabel('Cost (£)')
        plt.ylabel('Power Generated (mWh)')
        plt.title('Pareto Front Evolution Across Generations')
        plt.grid(True)
        plt.tight_layout()

        st.pyplot(plt)
        st.divider()

    def Plot_Cost_Convergence():
        #
        # Convergence of Cost
        # 
        plt.clf() 

        st.markdown("### Convergence of Cost")


        # Track the minimum cost over generations
        cost_history = [np.min(entry.pop.get("F")[:, 0]) for entry in st.session_state.result.history]
        plt.plot(cost_history, label="Min Cost")
        plt.xlabel("Generation")
        plt.ylabel("Cost")
        plt.title("Convergence of Cost")
        plt.grid(True)
        plt.legend()
    
        st.pyplot(plt)
        st.divider()

    def Plot_Power_Convergence():
        #
        # Convergence of Power Generated
        # 

        st.markdown("### Convergence of Power Generated")

        plt.clf() 
        y_history = [-np.max(entry.pop.get("F")[:, 1]) for entry in st.session_state.result.history]
        plt.plot(y_history)
        plt.xlabel("Generation")
        plt.ylabel("Power Generated (mWh)")
        plt.title("Convergence of Power Generated")
        plt.grid(True)
        plt.legend()

        st.pyplot(plt)
        st.divider()

        ###############################################################################

    def Plot_Hypervolume_Convergence():
        #
        # Convergence Via Hypervolume
        #

        st.markdown("### Convergence via Hypervolume")
        plt.clf() 
        ref_point = np.array([1e6, 1e6])  # Set based on your objective scales
        hv = HV(ref_point=ref_point)

        hv_history = [hv.do(entry.pop.get("F")) for entry in st.session_state.result.history]
        plt.plot(hv_history, label="Hypervolume")
        plt.xlabel("Generation")
        plt.ylabel("Hypervolume")
        plt.title("Convergence via Hypervolume")
        plt.grid(True)
        plt.legend()

        st.pyplot(plt)
        st.divider()
        ################################################################################

    def SurrogateModels_WithSHAP():
        #
        # Surrogate Model Summary
        #

        st.markdown("## SHAP Analysis of Surrogate Models for Objectives")

        Y_cost = []  # objective 1
        Y_power = [] # objective 2


        X = np.vstack(st.session_state.result.X)
        # print(X)
        F_all = np.vstack(st.session_state.result.F)
        Y_cost = F_all[:, 0]
        Y_power = F_all[:, 1]

        

        model_cost = xgb.XGBRegressor().fit(X, Y_cost)
        model_power = xgb.XGBRegressor().fit(X, Y_power)

        


        explainer_cost = shap.Explainer(model_cost, feature_perturbation="interventional")
        shap_values_cost = explainer_cost(X, check_additivity=False)

        explainer_power = shap.Explainer(model_power, feature_perturbation="interventional")
        shap_values_power = explainer_power(X, check_additivity=False)

        feature_names = [f"x{i}" for i in range(len(X[1]))]
        # print(len(feature_names))
        # print(len(X))

        st.markdown("### SHAP Summary Plot for Cost Objective")
        fig, ax = plt.subplots()
        shap.summary_plot(shap_values_cost, X, feature_names=feature_names, show=False)

        st.pyplot(fig)
        st.divider()

        st.markdown("### SHAP Summary Plot for Power Generation Objective")

        fig2, ax2 = plt.subplots()
        shap.summary_plot(shap_values_power, X, feature_names=feature_names, show=False)
        st.pyplot(fig2)
        st.divider()

        ################################################################################

        st.markdown("### SHAP Importance Heatmap for Cost Objective")

        # Use TreeExplainer for XGBoost models
        # Cost model
        explainer = shap.TreeExplainer(model_cost, feature_perturbation="interventional")
        shap_values = explainer.shap_values(X, check_additivity=False)   # X is your flattened schedule dataset

        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        heatmap_data = mean_abs_shap.reshape((st.session_state.nsga_params['days'], 3))

        # import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))
        sns.heatmap(heatmap_data, cmap="viridis")
        plt.xlabel("Action slot")
        plt.ylabel("Day")
        plt.title("SHAP Importance Heatmap")
        plt.show()

        sns.heatmap(heatmap_data, cmap="coolwarm")
        ax.grid(False)
        plt.title("SHAP Importance Heatmap for Cost Objective")
        st.pyplot(plt)
        st.divider()

        # sample_shap = shap_values[i].reshape((st.session_state.nsga_params['days'], 3))
        # sns.heatmap(sample_shap, cmap="coolwarm")


        ################################################################################

        st.markdown("### SHAP Importance Heatmap for Power Generation Objective")

        explainer = shap.TreeExplainer(model_power)
        shap_values = explainer.shap_values(X)   # X is your flattened schedule dataset

        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        heatmap_data = mean_abs_shap.reshape((st.session_state.nsga_params['days'], 3))

        plt.figure(figsize=(12, 6))
        sns.heatmap(heatmap_data, cmap="viridis")
        plt.xlabel("Action slot")
        plt.ylabel("Day")
        plt.title("SHAP Importance Heatmap")
        plt.show()

        sns.heatmap(heatmap_data, cmap="coolwarm")
        ax.grid(False)
        plt.title("SHAP Importance Heatmap for Power Generation Objective")
        st.pyplot(plt)
        st.divider()

    def ShowSchedules():
        # Converts the schedules into a more readable format
        def interpret_component(component_id):
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
            
        def interpret_action(action):
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
                total_turbines = 27
                max_action = 2 + components_per_turbine * total_turbines - 1

                if action < 2 or action > max_action:
                    raise Exception("Invalid action: out of bounds")
                    return "Invalid action: out of bounds"

                # Offset from first repair action
                maintenance_action["perform_maintenance"] = True
                offset = action - 2
                turbine_id = offset // components_per_turbine + 1
                component_id = offset % components_per_turbine + 1
                component = interpret_component(component_id)
                maintenance_action["maintenance_details"] = {"turbine_id": turbine_id, "component": component}


            return maintenance_action

        def ConvertScheduleToReadableFormat(schedule):
            readable_schedule = []
            for day in schedule:
                day_actions = []
                for action in day:
                    day_actions.append(interpret_action(action))
                readable_schedule.append(day_actions)
            return readable_schedule

        def TurnScheduleToIntActions(schedule):
            int_schedule = []
            for day in schedule:
                day_actions = []
                for action in day:
                    day_actions.append(int(action))
                int_schedule.append(day_actions)
            return int_schedule
        
<<<<<<< Updated upstream
        st.markdown("## Schedules from Final Population")
=======
        st.markdown("#### Schedules from Final Population")

        # CfD inputs
        col_strike, col_market = st.columns(2)
        with col_strike:
            strike_price = st.number_input("CfD Strike Price (£/MWh)", min_value=1, value=80)

        with col_market:
            market_price = st.number_input("Market Price (£/MWh)", min_value=1, value=50)

>>>>>>> Stashed changes
        # Flip power generation back to positive
        true_power = -st.session_state.result.F[:, 1]

        # Sort indices by ascending power
        sorted_indices = np.argsort(true_power)

        sorted_schedules = [st.session_state.result.X[i].reshape((st.session_state.nsga_params['days'], 3)) for i in sorted_indices]

        readable_schedules = [ConvertScheduleToReadableFormat(TurnScheduleToIntActions(schedule)) for schedule in sorted_schedules]

<<<<<<< Updated upstream
        st.session_state.schedule_index = st.selectbox(
            "Choose a schedule to display",
            options=list(range(len(sorted_schedules))),
            format_func=lambda i: f"Schedule {i+1}"
        )
        
        if st.session_state.get("schedule_index", None) is not None:
=======
        def schedule_comparison():
            st.markdown("### 🔄 Schedule Comparison")


            # Comparison of 2 schedules
            comp_col1, comp_col2 = st.columns(2)
>>>>>>> Stashed changes

            schedule_to_show = readable_schedules[st.session_state.schedule_index]
            st.markdown(f"### Schedule {st.session_state.schedule_index + 1} (Day View)")

            # Build a Gantt-friendly table
            for day_idx, day in enumerate(schedule_to_show):
                with st.expander(f"Day {day_idx + 1}"):
                    for action_idx, action in enumerate(day):
                        if action["return_to_port"]:
                            st.markdown(f"{action_idx} - 🔁 Return to port")
                            continue
                        elif action["do_nothing"]:
                            st.markdown(f"{action_idx} - ⏸ Do nothing")
                        elif action["perform_maintenance"]:
                            d = action["maintenance_details"]
                            st.markdown(f"{action_idx} - 🛠 Turbine {d['turbine_id']} — {d['component']}")

            st.markdown(f"### Schedule {st.session_state.schedule_index + 1} (Gantt View)")

<<<<<<< Updated upstream
            from datetime import datetime, timedelta
=======
            cost1, power1 = sched1["Cost"], sched1["Power"]/24
            cost2, power2 = sched2["Cost"], sched2["Power"]/24
>>>>>>> Stashed changes


        # Gantt chart generation
        if st.session_state.get("schedule_index", None) is not None:

<<<<<<< Updated upstream
            schedule_to_show = readable_schedules[st.session_state.schedule_index]

            gantt_rows = []

            # Base date for Day 1
            base_date = datetime(2026, 1, 1)
=======
            # Calculate profits
            profit1 = (strike_price - market_price) * (power1 * 24) - cost1 # convert power from MW to MWh
            profit2 = (strike_price - market_price) * (power2 * 24) - cost2
            profit_diff = profit2 - profit1
            profit_pct = (profit_diff / profit1 * 100) if profit1 != 0 else 0
>>>>>>> Stashed changes

            # Define the 3 action slot times
            slot_times = {
                0: timedelta(hours=9),   # 9am
                1: timedelta(hours=12),  # 12pm
                2: timedelta(hours=15),  # 3pm
            }

<<<<<<< Updated upstream
            for day_idx, day in enumerate(schedule_to_show):
                day_date = base_date + timedelta(days=day_idx)

                for slot_idx, action in enumerate(day):

                    # Only plot maintenance actions
                    if action["perform_maintenance"]:
                        d = action["maintenance_details"]
                        turbine = f"T{d['turbine_id']}"
                        component = d["component"]

                        start = day_date + slot_times[slot_idx]
                        finish = start + timedelta(hours=3)  # Assume each maintenance takes 3 hours

                        gantt_rows.append({
                            "Turbine": turbine,
                            "Component": component,
                            "Start": start,
                            "Finish": finish,
                            "Day": f"Day {day_idx + 1}"
                        })

            df = pd.DataFrame(gantt_rows)

            # fig = px.timeline(
            #     df,
            #     x_start="Start",
            #     x_end="Finish",
            #     y="Turbine",
            #     color="Component",
            #     hover_data=["Day"],
            #     title="Maintenance Timeline by Turbine",
            # )

            # Sort turbines numerically
            df["Turbine_num"] = df["Turbine"].str.extract(r'(\d+)').astype(int)
            df = df.sort_values("Turbine_num")

            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Turbine",
                color="Component",
                hover_data=["Day"],
                title="Maintenance Timeline by Turbine",
=======
            with colA:
                st.markdown(f"#### Schedule {schedule_one_index + 1}")
                st.metric("💰 Cost", f"£{cost1:,.2f}")
                st.metric("⚡ Avg Power", f"{power1:,.2f} MW")
                st.metric("💰 Profit", f"£{profit1:,.2f}")

            with colB:
                st.markdown(f"#### Schedule {schedule_two_index + 1}")
                st.metric("💰 Cost", f"£{cost2:,.2f}", delta=f"{cost_diff:,.2f} (£{cost_pct:+.1f}%)")
                st.metric("⚡ Avg Power", f"{power2:,.2f} MW", delta=f"{power_diff:,.2f} ({power_pct:+.1f}%)")
                st.metric("💰 Profit", f"£{profit2:,.2f}", delta=f"{profit_diff:,.2f} (£{profit_pct:+.1f}%)")
            
        def schedule_details():
            st.session_state.schedule_index = st.selectbox(
                "Choose a schedule to display details of below",
                options=list(range(len(sorted_schedules))),
                format_func=lambda i: f"Schedule {i+1}"
>>>>>>> Stashed changes
            )

<<<<<<< Updated upstream
            fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,        # move legend below the chart
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(b=80)  # add bottom margin so legend fits
            )
=======
                        <div class="optimised-badge">
                            Optimised for a window of {st.session_state.nsga_params['days']} days
                        </div>
                        """, unsafe_allow_html=True)

                    
                    cost = sorted_objectives.iloc[st.session_state.schedule_index]['Cost']
                    power = sorted_objectives.iloc[st.session_state.schedule_index]['Power']/24
                    profit1 = (strike_price - market_price) * (power * 24) - cost
                    power_lost = sorted_environnments[st.session_state.schedule_index].env.cumulative_power_lost / 1000

                    st.markdown(f"Power lost: {power_lost}")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(label="💰 Cost of performing maintenance", value=f"£{cost:,.2f}")

                    with col2:
                        st.metric(label="⚡ Average Power Generated", value=f"{power:,.2f} MW", delta=f"{(strike_price - market_price) * (power * 24):,.2f}")
                    
                    st.metric("💰 Profit", f"£{profit1:,.2f}")

                    def filter_schedule(schedule):
                        filtered = []

                        for day in schedule:
                            day_actions = []
                            for action in day:
                                day_actions.append(action)

                                # Stop processing this day if vessel returns to port
                                if action["return_to_port"]:
                                    day_actions.append(action)
                                    break

                            filtered.append(day_actions)

                        return filtered
                    
                    def schedule_day_view_block():

                        def action_idx_to_time(action_idx):
                            time_map = {
                                0: "09:00–12:00",
                                1: "12:00–15:00",
                                2: "15:00–18:00"
                            }
                            return time_map.get(action_idx, "Unknown time slot")


                        st.write(f"#### Day View")
                        # Build a Gantt-friendly table
                        with st.expander("Daily Actions"):
                            for day_idx, day in enumerate(schedule_to_show):
                                with st.expander(f"Day {day_idx + 1}", expanded=True):
                                    for action_idx, action in enumerate(day):
                                        if action["return_to_port"]:
                                            st.markdown(f"🔁 Return to port")
                                            break
                                        elif action["do_nothing"]:
                                            st.markdown(f"{action_idx_to_time(action_idx)} - ⏸ Do nothing")
                                        elif action["perform_maintenance"]:
                                            d = action["maintenance_details"]
                                            st.markdown(f"{action_idx_to_time(action_idx)} - 🛠 Turbine {d['turbine_id']} — {d['component']}")

                    def gantt_chart_view_block():
                    # Gantt chart generation
                        st.markdown(f"#### Gantt View")
                        with st.expander("Gantt-Chart"):
                            schedule_to_show = readable_schedules[st.session_state.schedule_index]
                            gantt_rows = []

                            # Base date for Day 1
                            base_date = datetime(2026, 1, 1)

                            # Define the 3 action slot times
                            slot_times = {
                                0: timedelta(hours=9),   # 9am
                                1: timedelta(hours=12),  # 12pm
                                2: timedelta(hours=15),  # 3pm
                            }

                            # st.write(schedule_to_show)

                            schedule_to_show = filter_schedule(schedule_to_show)

                            for day_idx, day in enumerate(schedule_to_show):
                                day_date = base_date + timedelta(days=day_idx)

                                for slot_idx, action in enumerate(day):

                                    # Only plot maintenance actions
                                    if action["perform_maintenance"]:
                                        d = action["maintenance_details"]
                                        turbine = f"T{d['turbine_id']}"
                                        component = d["component"]

                                        start = day_date + slot_times[slot_idx]
                                        finish = start + timedelta(hours=3)  # Assume each maintenance takes 3 hours

                                        gantt_rows.append({
                                            "Turbine": turbine,
                                            "Component": component,
                                            "Start": start,
                                            "Finish": finish,
                                            "Day": f"Day {day_idx + 1}"
                                        })

                            if len(gantt_rows) > 0:
                                df = pd.DataFrame(gantt_rows)

                                # Sort turbines numerically
                                df["Turbine_num"] = df["Turbine"].str.extract(r'(\d+)').astype(int)
                                df = df.sort_values("Turbine_num")

                                fig = px.timeline(
                                    df,
                                    x_start="Start",
                                    x_end="Finish",
                                    y="Turbine",
                                    color="Component",
                                    hover_data=["Day"],
                                    title="Maintenance Timeline by Turbine",
                                )

                                fig.update_layout(
                                    legend=dict(
                                        orientation="h",
                                        yanchor="top",
                                        y=-0.2,        # move legend below the chart
                                        xanchor="center",
                                        x=0.5
                                    ),
                                    margin=dict(b=80)  # add bottom margin so legend fits
                                )
>>>>>>> Stashed changes



            fig.update_yaxes(autorange="reversed")  # Gantt convention
            fig.update_layout(height=600, xaxis_title="Time")


            fig.update_yaxes(autorange="reversed")  # Plotly Gantt convention
            fig.update_layout(height=600, xaxis_title="Time")

            # ---------------------------
            # ADD SHADED BACKGROUND PER DAY
            # ---------------------------
            wave_df = pd.read_csv("data/daily_averages.csv")  # Assuming wave data is in this CSV file with 'date' and 'wave_height' columns
            wave_df["Hs"] = wave_df["Hs"].astype(float)
            wave_heights = wave_df["Hs"].tolist()
            max_wave = max(wave_heights)

            for day_idx, wave in enumerate(wave_heights):
                if(day_idx >= st.session_state.nsga_params['days']):
                    break
                # Compute the day's start and end timestamps
                day_start = base_date + timedelta(days=day_idx)
                day_end = day_start + timedelta(days=1)

                # Normalise wave height to opacity (0.1–0.4 looks good)
                opacity = 0.1 + 0.3 * (wave / max_wave)

                fig.add_shape(
                    type="rect",
                    x0=day_start,
                    x1=day_end,
                    y0=-0.5,
                    y1=df["Turbine"].nunique() - 0.5,
                    fillcolor=f"rgba(30, 144, 255, {opacity})",  # DodgerBlue tint
                    line_width=0,
                    layer="below"
                    )

            st.plotly_chart(fig, use_container_width=True)

        st.divider()



    Plot_Pareto_Final()
    Plot_Pareto_Generations()
    ShowSchedules()
    Plot_Cost_Convergence()
    Plot_Power_Convergence()
    Plot_Hypervolume_Convergence()
    SurrogateModels_WithSHAP()
            

