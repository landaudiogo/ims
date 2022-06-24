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


def read_input_excel(file_path: str): 
    sheets = pd.read_excel(file_path, sheet_name=None)
    months = pd.DataFrame({
        'Month': pd.Series(range(1, 13))
    })
    data_fr = sheets["fr"].loc[:, ["Family", " Target FR", "Critical FR"]]
    data_fr = data_fr.merge(months, how='cross')
    set_family = set(data_fr["Family"].unique())
    data_demand = sheets["demand"].loc[:, ["Family", "Month", "Demand", "Stdev Demand"]]
    set_family = set_family & set(data_demand["Family"].unique())
    data_cycle = sheets["cycle time"].loc[:, ["Family", "tbp (days)", "pd (days)", "lt"]]
    set_family = set_family & set(data_cycle["Family"].unique())
    data_cost = sheets["ind cust"].loc[:, ["Family", "Variable Cost/ Ton", "Fix Cost/ Ton"]]
    set_family = set_family & set(data_cost["Family"].unique())
    data_fam_importance = sheets["imp fam"].loc[:, ["Fam", "Revenue"]]
    data_fam_importance.columns = ["Family", "Revenue"]
    data_fam_importance.sort_values(["Revenue", "Family"])
    set_family = set_family & set(data_fam_importance["Family"].unique())
    data_production = sheets["xij"]
    set_family = set_family & set(data_production["Family"].unique())
    data_budget = sheets["bud"]
    data_capacity = sheets["capfj"]

    combined = data_fr.join(
        data_demand.set_index(['Family', 'Month']), on=['Family', 'Month']
    ).reset_index()
    missing_demand = combined['Demand'].isnull()
    combined.loc[missing_demand, 'Demand'] = 0
    combined.loc[missing_demand, 'Stdev Demand'] = 0
    combined = combined.join(data_cycle.set_index('Family'), on='Family')
    combined = combined.dropna()
    combined = combined.join(data_cost.set_index('Family'), on='Family')
    combined = combined.join(data_fam_importance.set_index("Family"), on="Family")
    combined = combined[combined["Family"].isin(set_family)]
    set_family = set_family & set(combined["Family"].unique())

    families = set_family
    family_list = []
    for family in families:
        daily_demand_list, daily_sigma_list = [], []
        family_subset = combined[combined['Family']==family]
        family_dp = family_subset['pd (days)'].iloc[0]
        family_tbp = family_subset['tbp (days)'].iloc[0]
        family_lt = family_subset['lt'].iloc[0]
        family_tfr = family_subset[' Target FR'].iloc[0]
        family_cfr = family_subset['Critical FR'].iloc[0]
        family_vcost = family_subset['Variable Cost/ Ton'].iloc[0]
        family_fcost = family_subset['Fix Cost/ Ton'].iloc[0]
        family_ind_cost = family_vcost + family_fcost
        family_importance = family_subset["Revenue"].iloc[0]
        for month in range(1, 13): 
            days_in_month = calendar.monthrange(2022, month)[1]
            [[d, s]] = family_subset.loc[
                (family_subset['Month'] == month), ['Demand', 'Stdev Demand']
            ].to_numpy()
            daily_demand = d/days_in_month
            daily_sigma = s/(days_in_month**(1/2))
            # print(d, s, daily_demand, daily_sigma)
            for day in range(days_in_month):
                daily_demand_list.append(daily_demand)
                daily_sigma_list.append(daily_sigma)

        family_list.append(Family(
            family_id=family,
            daily_demand=daily_demand_list,
            daily_sigma=daily_sigma_list,
            dp=family_dp,
            tbp=family_tbp,
            lt=family_lt,
            tfr=family_tfr,
            cfr=family_cfr,
            ind_cost=family_ind_cost,
            revenue=family_importance
        ))
    family_list = sorted(family_list, key=cmp_families, reverse=True)

    data_production = data_production.set_index("Family").loc[
        data_fam_importance[data_fam_importance["Family"].isin(set_family)]["Family"]
    ]
    production_mat = data_production.T.to_numpy()

    plant_list = []
    for (plant, rv) in zip(data_capacity.to_dict("records"), production_mat): 
        plant_list.append(Plant(
            plant["Plant"], 
            plant["Tons/ year"],
            family_list, 
            rv
        ))

    budget = data_budget.iloc[0, 0]

    return {
        "family_list": family_list, 
        "budget": budget,
        "production_df": data_production,
        "plant_list": plant_list,
    }


def main(argc, argv): 
    res = read_input_excel(argv[1])
    families = res["family_list"]
    budget = res["budget"]
    production_df = res["production_df"]
    plants = sorted(res["plant_list"], key=cmp_plants) 

    budget_constraint = BudgetConstraint(families, budget)
    plant_constraint_list = [
        PlantConstraint(plant)
        for plant in plants
    ]
    plant_solver = RandomPlantConstraintSolver(plant_constraint_list)

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

    plant_solver.solve()
    budget_constraint.solve_for_fr()
    for family in families: 
        print(family.family_id, family.fr)

        


if __name__ == '__main__': 
    main(len(sys.argv), sys.argv)
