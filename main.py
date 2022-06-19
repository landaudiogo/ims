import sys
import calendar
import pandas as pd
import numpy as np 

from typing import List

from dstructures import Family


def calculate_ST_in(): 
    pass

def calculate_SS_in(): 
    pass

def calculate_BKG_in(): 
    pass

def calculate_sigma_in(): 
    pass

def calculate_SC_in(
    daily_demand_i: List[int], 
    start_day: int, 
    lt: int, 
): 
    return sum(
        daily_demand_i[start_day-1:start_day + lt]
    )

def calculate_family_SC(family: Family):
    SC_list = []
    n = 0
    while True: 
        start_day=n*(family.lt + family.dp)+1
        if start_day > 365: 
            break
        SC_list.append(
            calculate_SC_in(
                daily_demand_i=family.daily_demand,
                start_day=start_day,
                lt=family.lt
            )
        )
        n+=1

def get_families_from_excel(file_path: str): 
    sheets = pd.read_excel(file_path, sheet_name=None)
    months = pd.DataFrame({
        'Month': pd.Series(range(1, 13))
    })
    data_fr = sheets["fr"]
    data_fr = data_fr.merge(months, how='cross')
    data_demand = sheets["demand"]
    data_cycle = sheets["cycle time"]
    data_cost = sheets["ind cust"]
    combined = data_fr.join(
        data_demand.set_index(['Family', 'Month']), on=['Family', 'Month']
    ).reset_index()
    missing_demand = combined['Demand'].isnull()
    combined.loc[missing_demand, 'Demand'] = 0
    combined.loc[missing_demand, 'Stdev Demand'] = 0
    combined = combined.join(data_cycle.set_index('Family'), on='Family').dropna()
    combined = combined.join(data_cost.set_index('Family'), on='Family')
    families = combined.Family.unique()
    family_list = []
    for family in families:
        daily_demand_list, daily_sigma_list = [], []
        family_lt = combined[combined['Family']==family]['Lead Time (days)'].iloc[0]
        family_dp = combined[combined['Family']==family]['Prod Days'].iloc[0]
        family_tfr = combined[combined['Family']==family][' Target FR'].iloc[0]
        family_cfr = combined[combined['Family']==family]['Critical FR'].iloc[0]
        family_vcost = combined[combined['Family']==family]['Variable Cost/ Ton'].iloc[0]
        family_fcost = combined[combined['Family']==family]['Fix Cost/ Ton'].iloc[0]
        family_ind_cost = family_vcost + family_fcost
        for month in range(1, 13): 
            days_in_month = calendar.monthrange(2022, month)[1]
            [[d, s]] = combined.loc[
                (combined['Family'] == family)
                & (combined['Month'] == month), ['Demand', 'Stdev Demand']
            ].to_numpy()
            daily_demand = d/days_in_month
            daily_sigma = s/(days_in_month**(1/2))
            for day in range(days_in_month):
                daily_demand_list.append(daily_demand)
                daily_sigma_list.append(daily_sigma)
    
        family_list.append(Family(
            family_id=family,
            daily_demand=daily_demand_list,
            daily_sigma=daily_sigma_list,
            dp=family_dp,
            lt=family_lt,
            tfr=family_tfr,
            cfr=family_cfr,
            ind_cost=family_ind_cost,
        ))
    return family_list

def main(argc, argv): 
    families = get_families_from_excel(argv[1])

    for family in families:
        family.calculate_cycles()
        break

if __name__ == '__main__': 
    main(len(sys.argv), sys.argv)
