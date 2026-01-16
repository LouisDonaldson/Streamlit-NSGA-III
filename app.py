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
import json
from datetime import datetime, timedelta
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from classes.nsga_iii import NSGAIII_Interface
from classes.llm_interface import GPTSession

# Runtime analysis
# import cProfile
# import pstats
# import io

st.set_page_config(
    page_title="NSGA3 OSWOP Dashboard",
    page_icon="🌊"
)

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

class DataStream:
    def __init__(self):
        self.data = []
        self.all_data = []
        self.new_data = False
    
    def AddData(self, message):
        self.data.append(message)
        self.all_data.append(message)
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

    sim_data = nsga_interface.run(verbose=False)

    st.session_state.running = False
    st.session_state.simulation_finished = True

    return sim_data


st.badge("Under Construction", color="red")
st.warning("This application is still under development. Some features may not work as expected. This is a very computationally expensive application - A high number of evaluations may crash the application due to cloud service RAM limitations.")
# Title
st.title("NSGA3 OSWOP Dashboard")
st.subheader("NSGA-III Offshore Wind Farm Scheduling Optimisation Simulation Dashboard")

st.markdown("This application allows you to configure and run a simulation for optimising offshore wind farm scheduling for maintenance operations using the NSGA-III algorithm.")
st.markdown("There is also a Chatbot functionality to gain further insights into the results. Please see sidebar for more information (top left corner).")
st.markdown("For in-depth information on how to understand the graphs and the technical information relating to the models, please visit the link below.")
st.link_button("Further Information and documentation", "https://mammoth-cough-70c.notion.site/OSW-NSGA-III-Environment-2-0-2df063e6bdf280dcb0e9f2410734c92a")

st.divider()

# Configuration box
# If simulation not started, show configuration box
if st.session_state.show_parameters == True:
    st.header("Simulation Configuration")

    # Input fields
    st.markdown("The default parameters currently set are for fast results.")
    max_generations = st.number_input("Maximum Generations (1-500)", min_value=1, max_value=500, value=100)
    population_size = st.number_input("Population Size (1-500)", min_value=1, max_value=500, value=40)
    
    days = st.number_input("Days (1-28)", min_value=1, value=7, max_value=28)

    start_day = st.slider(f"Select start day (max value is {365 - days} days)", min_value=0, max_value=365 - days, value=0 )

    def display_wave_height_graph(days):
        # Visualise wave height average and choose which weather window will be chosen.
        wave_df = pd.read_csv("data/daily_averages.csv")  # Assuming wave data is in this CSV file with 'date' and 'wave_height' columns
        wave_df["Hs"] = wave_df["Hs"].astype(float)
    
        window = days  # e.g., 7‑day execution window
        wave_df["highlight"] = wave_df["day_number"].between(start_day, start_day + window)
        chart = (
            alt.Chart(wave_df)
            .mark_bar()
            .encode(
                x=alt.X("day_number:O", title="Day of Year"),
                y=alt.Y("Hs:Q", title="Avg Wave Height (m)"),
                color=alt.condition(
                    "datum.highlight == true",
                    alt.value("#ff7f0e"),   # highlighted bars
                    alt.value("#1f77b4")    # normal bars
                ),
                tooltip=["day_number", "Hs"]
            )
        )

        st.altair_chart(chart, use_container_width=True)
    

    def display_wind_graph(days):
        # Visualise wave height average and choose which weather window will be chosen.
        df = pd.read_csv("data/mast_hourly_avg.csv")  # Assuming wave data is in this CSV file with 'date' and 'wave_height' columns

        # Parse timestamp
        df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])

        # Extract day of year
        df["day_number"] = df["TIMESTAMP"].dt.dayofyear

        # Choose the wind speed column you want to average
        wind_col = "ANx_80_WS_Avg"

        # Compute daily average wind speed
        daily_df = (
            df.groupby("day_number")[wind_col]
            .mean()
            .reset_index()
            .rename(columns={wind_col: "wind_speed"})
        )

        window = days
        daily_df["highlight"] = daily_df["day_number"].between(start_day, start_day + window)

        # Build Altair chart (matching your wave_df style)
        chart = (
            alt.Chart(daily_df)
            .mark_bar()
            .encode(
                x=alt.X("day_number:O", title="Day of Year"),
                y=alt.Y("wind_speed:Q", title="Avg Wind Speed (m/s)"),
                color=alt.condition(
                    "datum.highlight == true",
                    alt.value("#ff7f0e"),   # highlighted bars
                    alt.value("#1f77b4")    # normal bars
                ),
                tooltip=["day_number", "wind_speed"]
            )
            .properties(
                title="Daily Average Wind Speed",
                width=700,
                height=400
            )
        )

        st.altair_chart(chart, use_container_width=True)

    with st.expander("Wave height graph", expanded=True):
        display_wave_height_graph(days)
    with st.expander("Wind speed graph", expanded=True):
        st.warning("REMINDER: There's currently a 72 day discrepency between both datasets. This needs sorting.")
        display_wind_graph(days)

    # 2015-09-10 23:00:00
    # 07/01/2015 16:00



    st.write(f"Maximum number of evaluations will be: ```{max_generations * population_size}```")

    st.session_state.auto_plot = st.checkbox("Auto-run visualisation after optimisation finishes", value=True)

    params = {
        "generations": max_generations,
        "population_size": population_size,
        "days": days,
        "start_day": start_day,
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
    st.session_state.nsga_data = []
    # st.session_state.sim_envs = []

   

    st.session_state.result = start_simulation(
        st.session_state.nsga_params,
        st.session_state.data_stream
    )

    # Runtime analysis
    # pr = cProfile.Profile()
    # pr.enable()
    # ## put thing to evaluate here
    # pr.disable()
    # s = io.StringIO()
    # ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    # ps.print_stats(20)  # top 20 slowest functions
    # print(s.getvalue())
    # st.code(s.getvalue())

    
    st.session_state.simulation_finished = True
    st.rerun()

#### Simulation has finished - render results
if(st.session_state.simulation_finished):
    # simulation finished. Show results below
    st.success("Simulation completed.")
    # results can be accessed through 'st.session_state.result'
    st.header("Results Visualization")
    
    if st.session_state.result.F is None:
        st.info('''No results have been found. Please reload the page and edit the model parameters''')
    else:
        # Flip power generation back to positive
        true_power = -st.session_state.result.F[:, 1]

        # Sort indices by ascending power
        sorted_indices = np.argsort(true_power)

        # Get sorted schedules and objectives
        sorted_schedules = [st.session_state.result.X[i].reshape((st.session_state.nsga_params['days'], 3)) for i in sorted_indices]
        sorted_objectives = st.session_state.result.F[sorted_indices]
        # sorted_environments = st.session_state.result.opt.get("env")[sorted_indices] # Uses too much RAM
        snapshots = st.session_state.result.opt.get("ep_snapshots")[sorted_indices] # Snapshots of information produced per day
        # st.write(snapshots[0])


        def Plot_Pareto_Final():
            #
            # Pareto Front of Final Population
            #
            plt.clf()

            plt.figure(figsize=(10, 6))
            plt.plot(sorted_objectives[:, 0], true_power[sorted_indices],
                    c='blue', marker="o", label="Pareto Front")

            # Compute a dynamic offset (2% of y-range)
            y_min, y_max = true_power.min(), true_power.max()
            offset = (y_max - y_min) * 0.02

            # Annotate each point with its sorted index
            for i, idx in enumerate(sorted_indices):
                x = st.session_state.result.F[idx, 0]      # Cost
                y = -st.session_state.result.F[idx, 1]     # Power generation

                plt.text(
                    x,
                    y + offset,                             # ← raise label above point
                    str(i + 1),
                    fontsize=10,
                    ha='center',
                    va='bottom'
                )

            plt.xlabel("Cost (£)")
            plt.ylabel("Power Generation (KW/h)")
            plt.title("Pareto Front with Sorted Indices")
            plt.grid(True)
            plt.legend()

            st.pyplot(plt)

        def Plot_Pareto_Generations():
            #
            # Pareto Front of Generations
            #
            plt.clf() 
            all_x = []
            all_y = []
            all_gen = []

            num_to_show = len(st.session_state.result.history)

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
            plt.plot(sorted_objectives[:, 0], true_power[sorted_indices], c='red', linewidth=2.5, label="Global Pareto Front")


            cbar = plt.colorbar(sc)
            cbar.set_label('Generation Index')

            plt.xlabel('Cost (£)')
            plt.ylabel('Power Generated (KWh)')
            plt.title('Pareto Front Evolution Across Generations')
            plt.grid(True)
            plt.tight_layout()

            st.pyplot(plt)

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
            plt.ylabel("Cost (£)")
            plt.title("Convergence of Cost")
            plt.grid(True)
            plt.legend()
        
            st.pyplot(plt)

        def Plot_Power_Convergence():
            #
            # Convergence of Power Generated
            # 

            st.markdown("### Convergence of Power Generated")

            plt.clf() 
            y_history = [-np.max(entry.pop.get("F")[:, 1]) for entry in st.session_state.result.history]
            plt.plot(y_history)
            plt.xlabel("Generation")
            plt.ylabel("Power Generated (KWh)")
            plt.title("Convergence of Power Generated")
            plt.grid(True)
            plt.legend()

            st.pyplot(plt)

            ###############################################################################

        def Plot_Hypervolume_Convergence():
            #
            # Convergence Via Hypervolume
            #

            st.markdown("### Convergence via Hypervolume")

            st.markdown('''Hypervolume convergence graphs are an informative way to understand 
                        how the model is progressing. It is the volume of objective space 
                        dominated by the current Pareto Front, which is measured relative to a reference point''')

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
            ################################################################################

        def Plot_GD_Convergence():
            st.markdown('''### Convergence via Generational Distance''')

            st.markdown('''Generational distance (GD) convergence shows a direct, quantitative 
                        visualisation of how close the algorithm is getting to the best known Pareto 
                        Front over time. It's a clear way to discover whether or not the model is actually 
                        converging towards high quality trade-offs.
                        As the GD gets smaller, it shows how close the current Pareto sets are in terms to the reference front.''')

            all_f = []

            for algo in st.session_state.result.history:
                F = algo.pop.get("F")   # shape (n_pop, n_obj)
                all_f.append(F)

            # Stack into one big array
            all_f = np.vstack(all_f)

            nds = NonDominatedSorting()
            I = nds.do(all_f, only_non_dominated_front=True)
            ref_front = all_f[I]

            mins = ref_front.min(axis=0)
            maxs = ref_front.max(axis=0)

            def normalise(F):
                return (F - mins) / (maxs - mins + 1e-12)

            def compute_gd(front_gen, ref_front):
                diff = front_gen[:, None, :] - ref_front[None, :, :]
                dist = np.linalg.norm(diff, axis=2)
                min_dist = dist.min(axis=1)
                return min_dist.mean()

            gd_history = []

            ref_norm = normalise(ref_front)

            # IMPORTANT: recompute fronts per generation
            fronts = []
            for algo in st.session_state.result.history:
                F = algo.pop.get("F")
                I = nds.do(F, only_non_dominated_front=True)
                fronts.append(F[I])

            for F in fronts:
                F_norm = normalise(F)
                gd = compute_gd(F_norm, ref_norm)
                gd_history.append(gd)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(gd_history))),
                y=gd_history,
                mode="lines+markers",
                name="GD"
            ))

            fig.update_layout(
                title="Generational Distance Convergence",
                xaxis_title="Generation",
                yaxis_title="GD (lower is better)"
            )

            st.plotly_chart(fig, use_container_width=True)
            plt.clf()
    
        def SurrogateModels_WithSHAP():
            #
            # Surrogate Model Summary
            #

            st.markdown("## SHAP Analysis of Surrogate Models for Objectives")
            st.markdown('''SHAP (SHapley Additive exPlanations) is a method of creating explainability 
                        of machine-learning predictions. Is uses ideas from game theory to 
                        assign each feature in a model a 'fair share' of responsibility for a model's output. 
                        It shows how each feature contributes to a prediction, positively or negatively and by how much.''')

            if "shap_computed" not in st.session_state:
                if st.button("Compute SHAP Values"):
                    st.session_state.shap_computed = True
                    st.rerun()
                st.warning("Computing the SHAP values can take a few minutes depending on the dataset size. Please click the button to start the computation.")
            else:
                Y_cost = []  # objective 1
                Y_power = [] # objective 2

                X = []
                F_all = []


                X = np.vstack([h.pop.get("X") for h in st.session_state.result.history])            
                print(len(X))
                # print(X)
                F_all = np.vstack([h.pop.get("F") for h in st.session_state.result.history])
                Y_cost = F_all[:, 0]
                Y_power = F_all[:, 1]

                st.session_state.shap_model_cost = xgb.XGBRegressor().fit(X, Y_cost)
                st.session_state.shap_model_power = xgb.XGBRegressor().fit(X, Y_power)

                st.session_state.explainer_cost = shap.Explainer(st.session_state.shap_model_cost, feature_perturbation="interventional")
                shap_values_cost = st.session_state.explainer_cost(X, check_additivity=False)

                st.session_state.explainer_power = shap.Explainer(st.session_state.shap_model_power, feature_perturbation="interventional")
                shap_values_power = st.session_state.explainer_power(X, check_additivity=False)

                feature_names = [f"x{i}" for i in range(len(X[1]))]
                # print(len(feature_names))
                # print(len(X))

                st.markdown("### SHAP Summary Plot for Cost Objective")
                st.markdown('''SHAP summary graphs like seen in the image below are a 
                            breakdown of the X (action in a schedule) and it's impact on 
                            influencing the model in terms of cost.''')
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
                st.markdown('''These heatmaps shows how the model has interpreted the importance 
                            of each action slot across the 7 day schedule.''')

                # Use TreeExplainer for XGBoost models
                # Cost model
                explainer = shap.TreeExplainer(st.session_state.shap_model_cost, feature_perturbation="interventional")
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

                explainer = shap.TreeExplainer(st.session_state.shap_model_power)
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

        def turbine_health_heatmap(schedule_num):
            def extract_t_health_from_snapshot(snapshot):
                turbine_health = []
                for s in snapshot:
                    # st.write(snapshot)
                    turbine_health.append(s["t_health"])
                    
                df = pd.DataFrame(turbine_health)
                heatmap_df = df.T

                n_turbines = heatmap_df.shape[0]
                n_days = heatmap_df.shape[1]

                heatmap_df.index = [f"Turbine {i+1:02d}" for i in range(n_turbines)]
                heatmap_df.columns = [f"Day {i+1}" for i in range(n_days)]
                return heatmap_df

            df = extract_t_health_from_snapshot(snapshots[schedule_num])
            
            fig = px.imshow(
                df,
                color_continuous_scale=[
                    (0.0, "#d73027"),   # red
                    (0.5, "#fee08b"),   # yellow
                    (1.0, "#1a9850")    # green
                ],
                aspect="auto",
                labels=dict(x="Day", y="Turbine", color="Health"),
            )

            fig.update_layout(
                xaxis_side="top",
                margin=dict(l=60, r=20, t=60, b=20),
                coloraxis_colorbar=dict(
                    title="Health",
                    ticks="outside"
                )
            )

            
            st.plotly_chart(fig, use_container_width=True)

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
            
            st.markdown("#### Schedules from Final Population")
            col_strike, col_market = st.columns(2)
            with col_strike:
                strike_price = st.number_input("CfD Strike Price (£/MWh)", min_value=1, value=80)

            with col_market:
                market_price = st.number_input("Market Price (£/MWh)", min_value=0, value=50)

            st.metric("1 MWh Price", f"💵 {(strike_price - market_price) * 1} £/MWh")

            # Flip power generation back to positive
            true_power = -st.session_state.result.F[:, 1]


            # Sort indices by ascending power
            sorted_indices = np.argsort(true_power)

            sorted_schedules = [st.session_state.result.X[i].reshape((st.session_state.nsga_params['days'], 3)) for i in sorted_indices]
            sorted_objectives = pd.DataFrame([st.session_state.result.F[i] for i in sorted_indices], columns=["Cost", "Power"])

            sorted_objectives["Power"] = sorted_objectives["Power"].abs() / 1000
            sorted_objectives["Schedule"] = sorted_objectives.index

            # st.write(sorted_objectives)

            readable_schedules = [ConvertScheduleToReadableFormat(TurnScheduleToIntActions(schedule)) for schedule in sorted_schedules]

            def schedule_comparison():
                # Comparison of 2 schedules
                comp_col1, comp_col2 = st.columns(2)

                schedule_one_index = 0
                schedule_two_index = 1

                with comp_col1:
                    schedule_one_index = st.selectbox(
                        "🔍 Compare Schedule A",
                        index=schedule_one_index,
                        options=sorted_objectives["Schedule"],
                        format_func=lambda i: f"Schedule {i + 1}"
                    )

                remaining = [s for s in sorted_objectives["Schedule"] if s != schedule_one_index]
                
                with comp_col2:
                    schedule_two_index = st.selectbox(
                        "🔍 Compare Schedule B",
                        index=len(remaining)-1,
                        options=remaining,
                        format_func=lambda i: f"Schedule {i+1}"
                    )
                
                # Retrieve objective values for each selected schedule
                sched1 = sorted_objectives[sorted_objectives["Schedule"] == schedule_one_index].iloc[0]
                sched2 = sorted_objectives[sorted_objectives["Schedule"] == schedule_two_index].iloc[0]

                cost1, power1 = sched1["Cost"], sched1["Power"]
                cost2, power2 = sched2["Cost"], sched2["Power"]

                # Compute differences
                cost_diff = cost2 - cost1
                power_diff = power2 - power1

                # Avoid division by zero
                cost_pct = (cost_diff / cost1 * 100) if cost1 != 0 else 0
                power_pct = (power_diff / power1 * 100) if power1 != 0 else 0

                # CfD inputs
                st.markdown("### 🔄 Schedule Comparison")

                

                # Calculate profits
                profit1 = (strike_price - market_price) * power1 - cost1
                profit2 = (strike_price - market_price) * power2 - cost2
                profit_diff = profit2 - profit1
                profit_pct = (profit_diff / profit1 * 100) if profit1 != 0 else 0

                # Layout
                colA, colB = st.columns(2)

                with colA:
                    st.markdown(f"#### Schedule {schedule_one_index + 1}")
                    st.metric("💰 Cost", f"£{cost1:,.2f}")
                    st.metric("⚡ Power", f"{power1:,.2f} MWh")
                    st.metric("💰 Profit", f"£{profit1:,.2f}")

                with colB:
                    st.markdown(f"#### Schedule {schedule_two_index + 1}")
                    st.metric("💰 Cost", f"£{cost2:,.2f}", delta=f"£{cost_diff:,.2f} (£{cost_pct:+.1f}%)")
                    st.metric("⚡ Power", f"{power2:,.2f} MWh", delta=f"{power_diff:,.2f} ({power_pct:+.1f}%)")
                    st.metric("💰 Profit", f"£{profit2:,.2f}", delta=f"£{profit_diff:,.2f} (£{profit_pct:+.1f}%)")
                
            def schedule_details():
                st.session_state.schedule_index = st.selectbox(
                    "Choose a schedule to display details of below",
                    options=list(range(len(sorted_schedules))),
                    format_func=lambda i: f"Schedule {i+1}"
                )
                
                if st.session_state.get("schedule_index", None) is not None:
                    schedule_to_show = readable_schedules[st.session_state.schedule_index]
                    with st.expander("Schedule Details", expanded=True):
                        
                        st.markdown(f"### Schedule {st.session_state.schedule_index + 1}")
                        
                        st.markdown(f"""
                            <style>
                            .optimised-badge {{
                                display: inline-block;
                                background: linear-gradient(135deg, #2196f3, #21cbf3);
                                color: white;
                                padding: 0.4rem 0.8rem;
                                border-radius: 20px;
                                font-weight: 600;
                                font-size: 0.95rem;
                                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                                margin-bottom: 1rem;
                            }}
                            </style>

                            <div class="optimised-badge">
                                Optimised for a window of {st.session_state.nsga_params['days']} days
                            </div>
                            """, unsafe_allow_html=True)

                        
                        cost = sorted_objectives.iloc[st.session_state.schedule_index]['Cost']
                        power = sorted_objectives.iloc[st.session_state.schedule_index]['Power']
                        profit1 = (strike_price - market_price) * power - cost

                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric(label="💰 Cost of performing maintenance", value=f"£{cost:,.2f}")

                        with col2:
                            st.metric(label="⚡ Power Generated", value=f"{power:,.2f} MWh")
                        
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



                                    fig.update_yaxes(autorange="reversed")  # Gantt convention
                                    fig.update_layout(height=600, xaxis_title="Time")


                                    fig.update_yaxes(autorange="reversed")  # Plotly Gantt convention
                                    fig.update_layout(height=600, xaxis_title="Time")

                                    # ---------------------------
                                    # ADD SHADED BACKGROUND PER DAY
                                    # ---------------------------
                                    wave_df = pd.read_csv("data/daily_averages.csv")  # Assuming wave data is in this CSV file with 'date' and 'wave_height' columns
                                    wave_df["Hs"] = wave_df["Hs"].astype(float)
                                    
                                    wave_heights = (
                                        wave_df.loc[
                                            wave_df["day_number"].between(st.session_state.nsga_params['start_day'], st.session_state.nsga_params['start_day'] + st.session_state.nsga_params['days'] ),
                                            "Hs"
                                        ].tolist()
                                    )

                                    wave_heights_df = pd.DataFrame({
                                        "day_number": range(len(wave_heights)),
                                        "Hs": wave_heights
                                    })

                                    chart = (
                                        alt.Chart(wave_heights_df)
                                        .mark_bar()
                                        .mark_bar(color="#ff7f0e")
                                        .encode(
                                            x=alt.X("day_number:O", title="Day in schedule"),
                                            y=alt.Y("Hs:Q", title="Wave Height (m)"),
                                            tooltip=["day_number", "Hs"]
                                        )
                                    )

                                    with st.expander("Wave Heights During Scheduled Days"):
                                        st.altair_chart(chart, use_container_width=True)

                                    max_wave = 1.5

                                    for day_idx, wave in enumerate(wave_heights):
                                        if day_idx >= st.session_state.nsga_params['days']:
                                            break

                                        day_start = base_date + timedelta(days=day_idx)
                                        day_end = day_start + timedelta(days=1)

                                        t = min(wave / max_wave, 1.0)
                                        r = int((1 - t) * 80  + t * 255)
                                        g = int((1 - t) * 200 + t * 80)
                                        b = int((1 - t) * 120 + t * 80)

                                        # if wave > max_wave:
                                        #     r, g, b = 255, 80, 80
                                        # else:
                                        #     r, g, b = 80, 200, 120

                                        fig.add_vrect(
                                            x0=day_start,
                                            x1=day_end,
                                            fillcolor=f"rgb({r}, {g}, {b})",
                                            opacity=0.75,
                                            layer="below",
                                            line_width=0
                                        )






                                    st.plotly_chart(fig, use_container_width=True)

                                    st.markdown("""
                                        ### 🌊 Wave Height Gradient Legend

                                        <div style="margin-top: 10px;">

                                        <!-- Gradient bar -->
                                        <div style="
                                            height: 20px;
                                            width: 300px;
                                            background: linear-gradient(to right,
                                                rgb(80, 200, 120),
                                                rgb(200, 200, 80),
                                                rgb(255, 80, 80)
                                            );
                                            border-radius: 6px;
                                            margin-bottom: 6px;
                                        "></div>

                                        <!-- Labels -->
                                        <div style="display: flex; justify-content: space-between; width: 300px;">
                                            <span>0.0 m</span>
                                            <span>~0.75 m</span>
                                            <span>1.5 m+</span>
                                        </div>

                                        </div>

                                        <br>

                                        #### Interpretation
                                        - **Green** → calm, safe wave conditions  
                                        - **Yellow** → moderate wave height  
                                        - **Red** → unsafe (Hs ≥ 1.5 m)  
                                        - Colours are interpolated smoothly based on daily Hs  
                                        """, unsafe_allow_html=True)
                                else:
                                    st.info("Nothing has being scheduled so the Gantt-chart can not be rendered")
                        
                        schedule_day_view_block()
                        gantt_chart_view_block()
                        
                        with st.expander("Turbine Health Heatmap"):
                            turbine_health_heatmap(st.session_state.schedule_index)

            if len(sorted_schedules) > 1:
                schedule_comparison()
                
            schedule_details()
        
        ## plot pareto
        st.markdown("### Pareto Front of Final Population")
        if "plot_pareto" in st.session_state or st.session_state.auto_plot:
            Plot_Pareto_Final()
            st.divider()
        else:
            if st.button("Plot Final Pareto Front Graph"):
                st.session_state.plot_pareto = True
                st.rerun()

        ## plot pareto generations
        st.markdown("### Pareto Front Evolution Across Generations")
        if "plot_pareto_generations" in st.session_state or st.session_state.auto_plot:
            Plot_Pareto_Generations()
            st.divider()
        else:
            if st.button("Plot Pareto Front Evolutions Across Generations"):
                st.session_state.plot_pareto_generations = True
                st.rerun()
        
        ## show schedules
        st.markdown('''### Schedule Details''')
        if "show_schedules" in st.session_state or st.session_state.auto_plot:
            ShowSchedules()
            st.divider()
        else:
            if st.button("See Schedule Details"):
                st.session_state.show_schedules = True
                st.rerun()
        
        ## Plot convergences
        st.markdown("### Convergence Visualisation")
        st.markdown('''Convergence graphs show how the NSGA optimisation model 
                        improves its solutions over time.''')
        if "plot_objective_convergence" in st.session_state or st.session_state.auto_plot:
            Plot_Cost_Convergence()
            Plot_Power_Convergence()
            st.divider()
        else:
            if st.button("Plot Objective Convergences"):
                st.session_state.plot_objective_convergence = True
                st.rerun()

        if "plot_additional_convergence" in st.session_state:
            Plot_Hypervolume_Convergence()
            # Plot_GD_Convergence()
            st.divider()
        else:
            # st.error("Be aware, plotting the technical convergence graphs can crash the application. Only run when app hosted locally.")
            if st.button("Plot Technical Convergences"):
                st.session_state.plot_additional_convergence = True
                st.rerun()
        
        SurrogateModels_WithSHAP()


## Chatbot Sidebar
def GPT_Handler():

    # --- Session State Setup ---
    if "api_key" not in st.session_state:
        st.session_state.api_key = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                width: clamp(260px, 25vw, 380px) !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                width: clamp(260px, 25vw, 380px) !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # --- Sidebar UI ---
    with st.sidebar:
        st.title("💬 GPT Chatbot")
        with st.expander("ℹ️ About this ChatBot"):
            st.markdown('''Use this functionality to ask questions about the data produced by the model. It can be made aware of the data by clicking ```Initialise ChatGPT with simulation data```''')
            st.markdown('''Please be aware that it is not aware of any further processed data, including the SHAP or surrogate model data.''')
        # Step 1: Ask for API key if missing
        if not st.session_state.api_key:
            api_key_input = st.text_input(
                "Enter your API key",
                type="password",
                placeholder="sk-...",
            )

            if api_key_input:
                st.session_state.api_key = api_key_input
                st.rerun()

            st.stop()  # Prevents chatbot from rendering until key is set

        # Step 2: Show chat once API key exists
        st.success("API key loaded")

        if "gpt_data_initialised" in st.session_state:
            if st.session_state.gpt_data_initialised:
                st.info("GPT initialised with simulation data.") 

        if "gpt_session" not in st.session_state:
            st.session_state.gpt_session = GPTSession(api_key=st.session_state.api_key)
        # Display chat history
        for msg in st.session_state.gpt_session.messages[1:]:
            role = "assistant" if msg["role"] == "assistant" else "user"
            with st.chat_message(role):
                st.write(msg["content"])
                st.divider()

        # User input
        user_input = st.chat_input("Ask me something...")
        if st.session_state.simulation_finished:
            if "gpt_data_initialised" not in st.session_state:
                if st.button("Initialise GPT with simulation data"):
                    summary_text = f"Your job is to be an assistant to the person who will be sending the following messages in regards to understanding the data provided shortly, which was produced from a model. The short summary of how the model works: 'The simulation has completed with {len(st.session_state.result.F)} solutions in the final population. The objectives were cost and power generation over a period of {st.session_state.nsga_params['days']} days starting from day {st.session_state.nsga_params['start_day']} of the year. The Pareto front shows the trade-off between minimizing cost and maximizing power generation. The surrogate models were built using XGBoost and analyzed with SHAP to understand feature importance. Key insights include how different maintenance schedules impact both objectives.' The following is all of the data relating to the optimisation: '{json.dumps(st.session_state.nsga_data, indent=2)}' If you understand this, please can you reply with just 'I am up to date on the data. How can I help? :)'" 
                    # st.write(summary_text)
                    st.session_state.gpt_session.chat(summary_text)
                    st.session_state.gpt_data_initialised = True
                    st.rerun()
                    

        if user_input:
            # # Save user message
            st.session_state.gpt_session.chat(user_input)

            # st.session_state.messages.append({"role": "user", "content": user_input})

            # # Replace this with your real GPT call using st.session_state.api_key
            # assistant_reply = f"(Pretend GPT) You said: {user_input}"

            # # Save assistant reply
            # st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

            st.rerun()

GPT_Handler()


