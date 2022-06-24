import numpy as np

from typing import List
from dstructures import Family


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


    def __init__(self, plant): 
        self.plant = plant
        self.families = plant.families

    def validate_constraint(self): 
        rv = np.array([self.plant.production_rv])
        cv = np.array([
            [family.ST for family in self.plant.families]
        ]).T
        produce = rv.dot(cv).item()
        prod_families = [self.families[i].family_id 
            for i, prod in enumerate(self.plant.production_rv)
                if prod >= 1e-6
        ]
        return produce < self.plant.capacity

    def get_next_idx(self, i):
        for i in range(i-1, -2, -1): 
            if i == -1: 
                raise IndexError()
            if self.plant.production_rv[i] >= 1e-6: 
                return i


class PlantConstraintSolver: 


    def __init__(self, plant_constraints): 
        self.plant_constraints = plant_constraints


class RandomPlantConstraintSolver(PlantConstraintSolver): 


    def solve(self): 
        for plant_constraint in self.plant_constraints: 
            plant_constraint.solve_for_fr()



class AdvancedPlantConstraintSolver: 
    pass
