import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.optimize import minimize
from pymoo.problems import get_problem
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.visualization.scatter import Scatter
import json as json
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import random # random number generation
import streamlit as st

import matplotlib.pyplot as plt
from prettytable import PrettyTable

from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.algorithms.moo.sms import SMSEMOA
from pymoo.algorithms.moo.mopso_cd import MOPSO_CD



from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.core.callback import Callback
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from classes.data_handler import DataHandler as _data_handler
from classes.osw_environment_new import Environment as Environment
from classes.environment_handler import EnvironmentHandler

class Callback(Callback):
    def __init__(self, threshold=0.1, stream=None, termination_condition = {}, st=st):
        super().__init__()
        self.st = st
        self.termination_condition = termination_condition
        self.threshold = threshold
        self.stream = stream

    def notify(self, algorithm):

        F = algorithm.pop.get("F")
        fronts = NonDominatedSorting().do(F, only_non_dominated_front=True)
        non_dominated = algorithm.pop[fronts]


        # print(algorithm.termination.perc)
        gen = algorithm.n_gen
        f_vals = algorithm.pop.get("F")
        best_f1 = f_vals[:, 0].min()
        x_list = algorithm.pop.get("X")

        self.st.session_state.current_log = f"| {algorithm.termination.perc * 100}% complete | Generation: {gen} | Eps: {algorithm.output.eps.value} |"
        self.st.code(self.st.session_state.current_log, language="markdown")

        # self.st.rerun()

        data_to_add = {"generation": gen,
                        "best_f1": best_f1,
                        "non_dominated_sets": algorithm.opt.get("F").tolist(),
                        "current_dominating_sets": non_dominated.get("F").tolist(),
                        "n_evals": algorithm.evaluator.n_eval,
                        "eps": algorithm.output.eps.value,
                        "indicator": algorithm.output.indicator.value,
                        "perc": algorithm.termination.perc,
                        "schedule_actions": [[int(val) for val in row] for row in x_list]
                        }

        st.session_state.nsga_data.append(data_to_add)

        self.stream.AddData(data_to_add)
        
        # Manual escape clause
        # if best_f1 < self.threshold:
            # raise StopIteration("Escape triggered: f1 below threshold")

class WindFarmScheduling(ElementwiseProblem, _data_handler):
    def __init__(self, number_of_days, start_day, _stream=None, verbose=False, algo_params={}):
        self.number_of_days = number_of_days
        self.start_day = start_day
        self.data_handler = _data_handler()
        self.algo_params = algo_params
        
        st.session_state.current_log = f"Beginning data import..."
        st.code(st.session_state.current_log, language="markdown")

        self.data_handler.BeginImport()

        st.session_state.current_log = f"Data import completed."
        st.code(st.session_state.current_log, language="markdown")

        self.stream = _stream
        self.verbose=verbose
        # lower = [[0, 0, 0] for _ in range(365)]
        # upper = [[28, 28, 28] for _ in range(365)]
        # print(lower)
        
        super().__init__(
            n_var=number_of_days*3,          # Number of decision variables
            # xl = np.array(lower),  # Lower bounds
            # xu = np.array(upper),  # Upper bounds
            xl = np.zeros(self.number_of_days*3, dtype=int),  # Lower bounds
            xu = np.full(self.number_of_days*3, 163, dtype=int),  # Upper bounds

            n_obj = sum(1 for v in self.algo_params["objectives"].values() if v),
            n_ieq_constr = sum(1 for v in self.algo_params["constraints"].values() if v),

            # n_obj=2,          # Number of objectives
            # n_ieq_constr=1,   # Number of inequality constraints
        
        )

    def _evaluate(self, x, out, *args, **kwargs):
        env = EnvironmentHandler(x, data_handler=self.data_handler, number_of_days=self.number_of_days, _start_day=self.start_day, Environment=Environment, _stream = self.stream)
        
        env.RunSim(verbose=self.verbose)

        # Objectives
        env.reward["Power_Generated"]
        env.reward["Cost"]

        # Overall reward, not used
        env.reward["Overall"]

        # Constraint
        # g = sum(env.wave_height_violations)

        # # Out to NSGA
        # out["F"] = [env.reward["Cost"], -(env.reward["new_Power_Generated"])] 
        # out["G"] = [g]

        # Objectives
        F = []
        if self.algo_params["objectives"]["cost"]:
            F.append(env.reward["Cost"])
        if self.algo_params["objectives"]["energy"]:
            F.append(-(env.reward["new_Power_Generated"]))   
        if self.algo_params["objectives"]["rul_max"]:
            F.append(-(env.reward["RUL_Max"]))              

        # constraints
        G = []
        if self.algo_params["constraints"]["wave_height"]:
            G.append(sum(env.wave_height_violations))

        # Not implemented yet
        # if config["constraints"]["staff_availability"]:
        #     G.append(env.staff_availability_violation)      

        # Out to NSGA
        out["F"] = F
        out["G"] = G

        out["ep_snapshots"] = env.episode_snapshots

        # Save environments to access afterwards
        # out["env"] = env ## Uses far too much memory


class Optimiser_Interface:
    def __init__(self, nsga_params, _stream=None, st=st):
        self.generations = int(nsga_params['generations'])
        self.population_size = int(nsga_params['population_size'])
        self.start_day = int(nsga_params['start_day'])
        self.st = st
        self.result = None
        self.num_days = int(nsga_params['days'])
        self.stream = _stream
        self.algo_params = nsga_params["algorithm_params"]
        # self.run()

    def run(self, verbose=False):
        termination = DefaultMultiObjectiveTermination(
        xtol=1e-8,
        cvtol=1e-6,
        ftol=0.0025,
        period=30,
        n_max_gen=self.generations,
        n_max_evals=self.generations * self.population_size
        )

        problem = WindFarmScheduling(self.num_days, start_day=self.start_day, _stream=self.stream, verbose=verbose, algo_params=self.algo_params)

        print("Starting optimization")
        
        algo_choice = st.session_state.algorithm_params["algorithm"]["name"]
        # Map choice to algorithm
        if algo_choice == "NSGA-II":
            algorithm = NSGA2(pop_size=200)

        elif algo_choice == "NSGA-III":
            ref_dirs = get_reference_directions("das-dennis", n_dim=2, n_points=100)
            algorithm = NSGA3(pop_size=200, ref_dirs=ref_dirs)

        elif algo_choice == "MOEA/D":
            ref_dirs = get_reference_directions("das-dennis", n_dim=2, n_points=100)
            algorithm = MOEAD(ref_dirs=ref_dirs)

        elif algo_choice == "SMS-EMOA":
            algorithm = SMSEMOA(pop_size=200)

        elif algo_choice == "MOPSO-CD":
            inertia_weight = st.session_state.algorithm_params["algorithm"]["inertia_weight"]
            n_offsprings = st.session_state.algorithm_params["algorithm"]["n_offsprings"]
            algorithm = MOPSO_CD(pop_size=self.population_size, inertia_weight=inertia_weight, n_offsprings=n_offsprings)

        st.write(f"Running optimisation with: {algo_choice}")

        # algorithm = NSGA3(ref_dirs=ref_dirs, pop_size=self.population_size)

        result = minimize(problem,
                        algorithm,
                        termination,
                        callback=Callback(stream=self.stream, termination_condition = termination, st=self.st),
                        seed=42,
                        verbose=True,
                        save_history=True)
        
        return result
        # st.write(result.X.tolist())
        # data_to_add = {
        #             "completed": True,
        #             "schedule_actions": [[int(val) for val in row] for row in result.X.tolist()],
        #             "current_dominating_sets":result.F.tolist()
        #             }
        
        # self.stream.AddData(data_to_add)            
        
    

