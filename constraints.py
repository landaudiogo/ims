import numpy as np
import random

from typing import List
from dstructures import Family
from itertools import combinations

from utils import cmp_families


class Constraint: 


    def solve_for_fr(self): 
        i = len(self.families)-1
        while not self.validate_constraint(): 
            family = self.families[i]
            if family.fr > family.cfr:
                family.fr -= 0.01
            else: 
                i = self.get_next_idx(i)

    def validate_constraint(self): 
        raise NotImplementedError()

    def get_next_idx(self, i): 
        return i-1 


class BudgetConstraint(Constraint):

    def __init__(
        self, 
        sorted_families: List[Family], 
        budget: float,
    ):
        self.families = sorted_families
        self.budget = budget

    def validate_constraint(self): 
        total_cost = sum(map(
            lambda family: family.total_cost,
            self.families
        ))
        return total_cost <= self.budget


class PlantConstraint(Constraint): 


    def __init__(self, plant, families): 
        self.plant = plant
        self.families = families

    def __repr__(self): 
        return f"<PlantConstraint {self.plant}>"

    def validate_constraint(self): 
        rv = np.array([self.plant.production_rv])
        cv = np.array([
            [family.ST for family in self.families]
        ]).T
        produce = rv.dot(cv).item()
        prod_families = [self.families[i].family_id 
            for i, prod in enumerate(self.plant.production_rv)
                if prod >= 1e-6
        ]
        return produce < self.plant.capacity

    def get_next_idx(self, i):
        for k in range(i-1, -2, -1): 
            if k == -1: 
                raise IndexError()
            if self.plant.production_rv[k] >= 1e-6: 
                return k


class PlantConstraintSolver: 


    def __init__(self, plant_constraints): 
        self.plant_constraints = plant_constraints
        random.shuffle(self.plant_constraints)
        print(self.plant_constraints)

    def solve(self): 
        raise NotImplementedError()


class RandomPlantConstraintSolver(PlantConstraintSolver): 


    def solve(self): 
        for plant_constraint in self.plant_constraints: 
            plant_constraint.solve_for_fr()



class AdvancedPlantConstraintSolver(PlantConstraintSolver): 

    
    def solve(self): 
        failing_constraints = [pc
            for pc in self.plant_constraints
                if pc.validate_constraint() == False
        ]
        if len(failing_constraints) == 0: 
            return

        comb_list = [[], [], []]
        for i in [3, 2, 1]:
            num_comb = i
            comb = combinations(
                [j for j in range(len(failing_constraints))],
                num_comb
            )
            for idxs in comb: 
                universe = set()
                for pc in failing_constraints: 
                    universe |= pc.plant.family_set
                res = universe
                for idx in idxs: 
                    res &= failing_constraints[idx].plant.family_set
                if len(res): 
                    comb_list[3 - i].append(res)
        
        for set_list in comb_list: 
            for i, s in enumerate(set_list): 
                set_list[i] = min(s)

        min_list = [max(comb_mins, key=cmp_families) 
            for comb_mins in comb_list
                if comb_mins != []
        ]
        ref = min_list[0]
        tons_below_list = [pc.plant.tons_below(ref)
            for pc in failing_constraints
        ]
        print(tons_below_list)
        pc_index = tons_below_list.index(min(tons_below_list)) 
        print(pc_index)
        failing_constraints[pc_index].solve_for_fr()
        self.solve()

