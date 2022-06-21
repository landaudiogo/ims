from typing import List
from dstructures import Family


class Constraint: 


    def check_for_cfr(self): 
        raise NotImplementedError()

    def solve_for_fr(self): 
        raise NotImplementedError()

    def validate_constraint(self): 
        raise NotImplementedError()


class BudgetConstraint(Constraint):

    def __init__(
        self, 
        sorted_families: List[Family], 
        budget_per_ton: float,
    ):
        self.families = sorted_families
        self.budget_per_ton = budget_per_ton

    def solve_for_fr(self): 
        pass

    def validate_constraint(self): 
        total_budget = sum(map(
            lambda family: family.ST, 
            self.families
        ))*self.budget_per_ton
        total_cost = sum(map(
            lambda family: family.total_cost,
            self.families
        ))
        print(total_cost, total_budget)
        return total_cost <= total_budget



class PlantConstraint(Constraint): 
    pass
