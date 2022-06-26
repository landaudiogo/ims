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
    BudgetConstraint, PlantConstraint, RandomPlantConstraintSolver,
    AdvancedPlantConstraintSolver
)
from utils import cmp_families, cmp_plants
from exc import StrictCriticalFillRate
from parse_input import read_input_excel


def main(argc, argv): 
    df_list = []
    for fam_id in ["AMNNSM", "BRPBBG", "VRNNSM"]:
        for k in range(5, 365, 5): 
            print(f"=== {fam_id}-{k} ===")
            res = read_input_excel(argv[1], fam_id=fam_id, lt=k)

            families = res.family_list
            budget = res.budget
            production_df = res.production_df
            plants = res.plant_list

            budget_constraint = BudgetConstraint(families, budget)
            plant_constraint_list = [PlantConstraint(plant, families) for plant in plants]
            plant_constraint_solver = (
                RandomPlantConstraintSolver(plant_constraint_list)
                if argv[2] == "random" else AdvancedPlantConstraintSolver(plant_constraint_list)
            )

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
                if family.family_id == fam_id:
                    df_list.extend(family.get_cycle_list())


    res_df = pd.DataFrame(df_list, columns=[
        "family", "lt", "cycle", "start date", "end date", "FR", "ST",
        "SC", "SS", "BKG", "BKG Cost", "Lead Time", "COV", "revenue"
    ])
    res_df["rate"] = res_df["SS"]/res_df["ST"]
    print(res_df)
    test_df = res_df[["family", "lt", "ST", "rate", "COV"]]
    df_avg_rate = test_df.groupby(["family", "lt"]).aggregate({
        "ST": "sum", 
        "rate": "mean", 
        "COV": "mean",
    })
    df_avg_rate.to_excel(argv[3])


if __name__ == '__main__': 
    main(len(sys.argv), sys.argv)
