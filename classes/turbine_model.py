import random

class Farm:
    def __init__(self, num_turbines, exp_decay_list):
        self.exp_decay_list = exp_decay_list
        self.turbines = [Turbine(i, self.exp_decay_list[0]) for i in range(num_turbines)]
        
    def get_total_power(self, wind_speed):
        total_power = sum(turbine.get_power_produced(wind_speed) for turbine in self.turbines)
        return total_power
    
    def degrade_all(self, ub = 3, lb = 1):
        for turbine in self.turbines:
            for component in turbine.components.values():
                if isinstance(component, list):
                    for comp in component:
                        decrease = round(random.uniform(lb, ub))
                        try:
                            comp.degrade(self.exp_decay_list[self.exp_decay_list.index(comp.health) + decrease])
                        except Exception as e:
                            raise 
                            # comp.degrade(self.exp_decay_list[len(self.exp_decay_list) - 1])
        
                            # comp.degrade(amount)
                else:
                    decrease = round(random.uniform(lb, ub))
                    try:
                        component.degrade(self.exp_decay_list[self.exp_decay_list.index(component.health) + decrease])
                    except Exception as e:
                        raise
                        # component.degrade(self.exp_decay_list[len(self.exp_decay_list) - 1])

        
        # calculate overall turbine health
        for turbine in self.turbines:
            total_health = sum(comp.health if not isinstance(comp, list) else sum(c.health for c in comp) for comp in turbine.components.values())
            num_components = sum(1 if not isinstance(comp, list) else len(comp) for comp in turbine.components.values())
            turbine.overall_health = total_health / num_components

    def degrade_turbine(self, turbine_index, ub = 3, lb = 1):
        turbine = self.turbines[turbine_index]
        for component in turbine.components.values():
                if isinstance(component, list):
                    for comp in component:
                        decrease = round(random.uniform(lb, ub))
                        try:
                            comp.degrade(self.exp_decay_list[self.exp_decay_list.index(comp.health) + decrease])
                        except Exception as e:
                            raise 
                            # comp.degrade(self.exp_decay_list[len(self.exp_decay_list) - 1])
        
                            # comp.degrade(amount)
                else:
                    decrease = round(random.uniform(lb, ub))
                    try:
                        component.degrade(self.exp_decay_list[self.exp_decay_list.index(component.health) + decrease])
                    except Exception as e:
                        raise
                        # component.degrade(self.exp_decay_list[len(self.exp_decay_list) - 1])
        
        total_health = sum(comp.health if not isinstance(comp, list) else sum(c.health for c in comp) for comp in turbine.components.values())
        num_components = sum(1 if not isinstance(comp, list) else len(comp) for comp in turbine.components.values())
        turbine.overall_health = total_health / num_components

    def repair_component(self, turbine_index, component_name, increase_amount):
        turbine = self.turbines[turbine_index]
        component = turbine.components.get(component_name)
        if component:
            if isinstance(component, list):
                for comp in component:
                    if(self.exp_decay_list.index(comp.health) - increase_amount < 0):
                        
                        new_health = self.exp_decay_list[0]
                    else:
                        new_health = self.exp_decay_list[self.exp_decay_list.index(comp.health) - increase_amount]
                    comp.repair(new_health)
            else:
                if(self.exp_decay_list.index(component.health) - increase_amount < 0):
                        new_health = self.exp_decay_list[0]
                else:
                    new_health = self.exp_decay_list[self.exp_decay_list.index(component.health) - increase_amount]
                component.repair(new_health)
        
            # Recalculate overall health
            total_health = sum(comp.health if not isinstance(comp, list) else sum(c.health for c in comp) for comp in turbine.components.values())
            num_components = sum(1 if not isinstance(comp, list) else len(comp) for comp in turbine.components.values())
            turbine.overall_health = total_health / num_components
        else:
            raise ValueError(f"Component {component_name} not found in turbine {turbine_index}")
        
        return

class Turbine:
    def __init__(self, num, initial_health):
        self.num = num  # coordinate in terms of map from Google Earth 
        self.components = {
            "nacelle": Nacelle_Comp(),
            "blades": Blades_Comp(),
            "tower": Tower_Comp(),
            "generator": Generator_Comp(),
            "gearbox": Gearbox_Comp(),
            "control_system": ControlSystem_Comp()
        }
        self.num_components = len(self.components) + 2  # +2 for blades (3 blades counted as 1 component)
        self.overall_health = initial_health  # average health of all components

    def get_power_produced(self, wind_speed):
        # Placeholder for power production logic
        return 0


# component classes
class Component:
    def __init__(self, health=100):
        self.health = health
        self.status = self.Determine_Status(self.health)
        self.repair_time = {"corrective": 3,  # time in hours
                       "preventive": 2}


    def Determine_Status(self, health):
        status = ""
        if health <= 0:
            status = "failed"
        elif health < 50:
            status = "degraded"
        else:
            status = "operational"
        return status
    
    def degrade(self, new_health):
        # amount = round(random.uniform(lb, ub))
        self.health = new_health
        if self.health <= 0:
            self.health = 0
            self.status = "failed"
        elif self.health < 50:
            self.status = "degraded"

        return self.status

    def repair(self, new_health):
        
        self.health = new_health
        if self.health > 100:
            self.health = 100
        if self.health >= 50:
            self.status = "operational" 
        
        return self.status, self.health

 
    
class Nacelle_Comp(Component):
    def __init__(self, failure_rate=0.01):
        super().__init__()
        self.failure_rate = failure_rate

        self.repair_cost = {"corrective": {"lb": 20000, "ub": 35000}, "preventative": {"lb": 7000, "ub": 15000}}
       
        return
    
    
    
class Blades_Comp(Component):
    def __init__(self, failure_rate=0.01):
        super().__init__()
        self.failure_rate = failure_rate

        corrective_cost = 5000  # in dollars
        preventive_cost = 2000  # in dollars
        self.repair_cost = {"corrective": {"lb": 15000, "ub": 30000}, "preventative": {"lb": 4000, "ub": 10000}}
        return
    

class Tower_Comp(Component):
    def __init__(self, failure_rate=0.01):
        super().__init__()
        self.failure_rate = failure_rate

        corrective_cost = 5000  # in dollars
        preventive_cost = 2000  # in dollars
        self.repair_cost = {"corrective": {"lb": 8000, "ub": 20000}, "preventative": {"lb": 3000, "ub": 7000}}
        return
    

class Generator_Comp(Component):
    def __init__(self, failure_rate=0.01):
        super().__init__()
        self.failure_rate = failure_rate

        corrective_cost = 5000  # in dollars
        preventive_cost = 2000  # in dollars
        self.repair_cost = {"corrective": {"lb": 25000, "ub": 40000}, "preventative": {"lb": 8000, "ub": 15000}}
        return

class Gearbox_Comp(Component):
    def __init__(self, failure_rate=0.01):
        super().__init__()
        self.failure_rate = failure_rate

        corrective_cost = 5000  # in dollars
        preventive_cost = 2000  # in dollars
        self.repair_cost = {"corrective": {"lb": 50000, "ub": 95000}, "preventative": {"lb": 10000, "ub": 20000}}
        return
  

class ControlSystem_Comp(Component):
    def __init__(self, failure_rate=0.01):
        super().__init__()
        self.failure_rate = failure_rate

        corrective_cost = 5000  # in dollars
        preventive_cost = 2000  # in dollars
        self.repair_cost = {"corrective": {"lb": 5000, "ub": 12000}, "preventative": {"lb": 2000, "ub": 5000}}
        return
    
