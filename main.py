import sys
import calendar
import pandas as pd
import numpy as np 
import functools

from typing import List

from dstructures import (
    Family, Plant
)
from constraints import (
    BudgetConstraint, PlantConstraint, RandomPlantConstraintSolver
)
from utils import cmp_families, cmp_plants
from exc import StrictCriticalFillRate
from parse_input import read_input_excel


def main(argc, argv): 
    res = read_input_excel(argv[1])

    families = res.family_list
    budget = res.budget
    production_df = res.production_df
    plants = sorted(res.plant_list, key=cmp_plants) 

    budget_constraint = BudgetConstraint(families, budget)
    plant_constraint_list = [
        PlantConstraint(plant)
        for plant in plants
    ]
    plant_constraint_solver = RandomPlantConstraintSolver(plant_constraint_list)

    for family in families: 
        family.fr = family.cfr
    if budget_constraint.validate_constraint() == False: 
        raise StrictCriticalFillRate(
            "Budget Constraint is exceeded for the defined critical fill rates"
        )
    for plant_constraint in plant_constraint_list: 
        if plant_constraint.validate_constraint() == False: 
            raise StrictCriticalFillRate(
                "Plant Constraint is exceeded for the defined critical fill rates"
            )
    
    for family in families: 
        family.fr = family.tfr

    plant_constraint_solver.solve()
    budget_constraint.solve_for_fr()
    for family in families: 
        print(family.family_id, family.fr)

        


if __name__ == '__main__': 
    main(len(sys.argv), sys.argv)
