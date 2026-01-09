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
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.core.callback import Callback
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting



from classes.data_handler import DataHandler as _data_handler
from classes.osw_environment_new import Environment as Environment
from classes.environment_handler import EnvironmentHandler


class Callback(Callback):
    def __init__(self, threshold=0.1, stream=[], termination_condition = {}, st=st):
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

        self.stream.AddData(data_to_add)
        
        # Manual escape clause
        # if best_f1 < self.threshold:
            # raise StopIteration("Escape triggered: f1 below threshold")


class WindFarmScheduling(ElementwiseProblem, _data_handler):
    def __init__(self, number_of_days, start_day, _stream=None):
        self.number_of_days = number_of_days
        self.start_day = start_day
        self.data_handler = _data_handler()
        self.data_handler.BeginImport()
        self.stream = _stream
        # lower = [[0, 0, 0] for _ in range(365)]
        # upper = [[28, 28, 28] for _ in range(365)]
        # print(lower)
        super().__init__(
            n_var=number_of_days*3,          # Number of decision variables
            n_obj=2,          # Number of objectives
            n_ieq_constr=0,   # Number of inequality constraints
            # xl = np.array(lower),  # Lower bounds
            # xu = np.array(upper),  # Upper bounds
            xl = np.zeros(self.number_of_days*3, dtype=int),  # Lower bounds
            xu = np.full(self.number_of_days*3, 163, dtype=int)  # Upper bounds
 
        )

    def _evaluate(self, x, out, *args, **kwargs):
        env = EnvironmentHandler(x, data_handler=self.data_handler, number_of_days=self.number_of_days, _start_day=self.start_day, Environment=Environment, _stream = self.stream)

        env.RunSim(episodes=self.number_of_days, _start_day=self.start_day, verbose=False)
        # print(f"{env.reward}")
        env.reward["Power_Generated"]
        env.reward["Cost"]
        env.reward["Overall"]

        out["F"] = [float(env.reward["Cost"]), float(-env.reward["Power_Generated"])]


class NSGAIII_Interface:
    def __init__(self, nsga_params, _stream=None, st=st):
        self.generations = int(nsga_params['generations'])
        self.population_size = int(nsga_params['population_size'])
        self.start_day = int(nsga_params['start_day'])
        self.st = st
        self.result = None
        self.num_days = int(nsga_params['days'])
        self.stream = _stream
        # self.run()

    def run(self):
        termination = DefaultMultiObjectiveTermination(
        xtol=1e-8,
        cvtol=1e-6,
        ftol=0.0025,
        period=30,
        n_max_gen=self.generations,
        n_max_evals=self.generations * self.population_size
        )

        problem = WindFarmScheduling(self.num_days, start_day=self.start_day, _stream=self.stream)

        print("Starting optimization with NSGA-III...")

        ref_dirs = get_reference_directions("das-dennis", 2, n_partitions=self.population_size//2)
        algorithm = NSGA3(ref_dirs=ref_dirs, pop_size=self.population_size)

        result = minimize(problem,
                        algorithm,
                        termination,
                        callback=Callback(stream=self.stream, termination_condition = termination, st=self.st),
                        seed=42,
                        verbose=True,
                        save_history=True)
        
        data_to_add = {
                    "completed": True,
                    "schedule_actions": [[int(val) for val in row] for row in result.X.tolist()],
                    "current_dominating_sets":result.F.tolist()

                    }
        
        self.stream.AddData(data_to_add)            
        return result
    
    

