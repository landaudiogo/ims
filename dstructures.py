import functools

from typing import List, Optional
from dataclasses import dataclass
from scipy.optimize import fsolve
from statistics import NormalDist
from datetime import datetime

from exc import MissingContext

normdist = NormalDist(mu=0, sigma=1)


@functools.total_ordering
class Family:


    def __init__(
        self,
        family_id: str,
        daily_demand: List[int],
        daily_sigma: List[int],
        dp: int,
        tbp: int, 
        lt: int,
        tfr: int,
        cfr: int,
        ind_cost: int,
        revenue: float, 
        sp: float,
        fr: Optional[int] = None,
    ): 
        self.family_id = family_id
        self.daily_demand = daily_demand
        self.daily_sigma = daily_sigma
        self.tbp = int(tbp)
        self.dp = int(dp)
        self.lt = int(lt)
        self.tfr = tfr
        self.cfr = cfr
        self.ind_cost = ind_cost
        self.revenue = revenue
        self.sp = sp
        self.__fr = fr
        self.cycles = []
        self.set_cycles()

    def __hash__(self):
        return hash(self.family_id)

    def __eq__(self, other): 
        if not isinstance(other, self.__class__): 
            return False
        return self.family_id == other.family_id

    
    def __lt__(self, other): 
        if not isinstance(other, self.__class__): 
            raise Exception()
        if self.revenue != other.revenue: 
            return self.revenue < other.revenue
        else: 
            return self.family_id > other.family_id

    def __repr__(self): 
        return f"{self.family_id}"

    @property
    def total_cost(self): 
        return self.ST*self.ind_cost

    @property
    def ST(self): 
        return functools.reduce(
            lambda acc, cycle: acc+(cycle.SS + cycle.SC), 
            self.cycles, 0
        )

    @property
    def fr(self): 
        return self.__fr

    @fr.setter
    def fr(self, value: float): 
        self.__fr = value
        for i, cycle in enumerate(self.cycles): 
            cycle.fr = self.__fr

    def set_cycles(self): 
        start_day = 1
        while start_day <= 365: 
            cycle = Cycle(self.daily_demand, self.daily_sigma, start_day, self.lt)
            self.cycles.append(cycle)
            start_day += self.lt

    def get_cycle_list(self): 
        return [
            [
                self.family_id,
                self.lt,
                i,
                datetime.strptime(
                    "2022-" + str(cycle.start_day), "%Y-%j"
                ).strftime("%Y-%m-%d"),
                datetime.strptime(
                    "2022-" + str(min(cycle.start_day + cycle.lt, 365)), "%Y-%j"
                ).strftime("%Y-%m-%d"),
                self.fr,
                cycle.ST,
                cycle.SC, 
                cycle.SS, 
                cycle.BKG, 
                (self.sp - self.ind_cost)*cycle.BKG, 
                self.lt,
                (cycle.ST)/((cycle.ST + cycle.BKG)/cycle.lt), 
                self.revenue
            ]
            for i, cycle in enumerate(self.cycles)
        ]

class Cycle: 

    def __init__(
        self,
        daily_demand, 
        daily_sigma, 
        start_day, 
        lt,
        fr = None
    ): 
        self.start_day = start_day
        self.lt = lt
        self.SC = None
        self.calculate_SC(daily_demand, start_day, lt)
        self.sigma = None
        self.calculate_sigma(daily_sigma, start_day, lt)
        self.__fr = None
        self.BKG = None
        self.SS = None
        if fr != None: 
            self.__fr = fr
            self.calculate_SS_and_BKG()

    @property
    def fr(self): 
        return self.__fr

    @property
    def ST(self): 
        return self.SS + self.SC

    @fr.setter
    def fr(self, value: float): 
        self.__fr = value
        self.calculate_SS_and_BKG()

    def calculate_SC(self, daily_demand, start_day, lt): 
        self.SC = sum(daily_demand[start_day-1: start_day-1+lt])

    def calculate_sigma(self, daily_sigma, start_day, lt): 
        self.sigma = functools.reduce(
            lambda acc, val: acc+val**2, 
            daily_sigma[start_day-1: start_day-1+lt], 0
        )**(1/2)

    def calculate_SS_and_BKG(self): 
        self.SS, self.BKG = fsolve(
            self.solve_for_ss_and_bkg, 
            [0, 0], 
            args=(self.sigma, self.SC, self.fr),
            maxfev=10_000
        )

    @staticmethod
    def solve_for_ss_and_bkg(xv, sigma, sc, fr):
        global normdist
        if sigma == 0: 
            return (0, 0)
        return (
            (xv[0] + sc)/(xv[0] + sc + xv[1]) - fr,
            - xv[0]*(1 - normdist.cdf(xv[0]/sigma)) + sigma*normdist.pdf(xv[0]/sigma) - xv[1]
        )


class Plant: 


    def __init__(
        self, plant_id, capacity, families, production_rv
    ):
        self.plant_id = plant_id
        self.capacity = capacity
        self.production_rv = production_rv
        self.families = families
        self.family_set = set()
        for family, prod_rate in zip(families, production_rv): 
            if prod_rate > 1e-6: 
                self.family_set |= set([family])

    def __hash__(self): 
        return hash(self.plant_id)

    def __eq__(self, other): 
        if not isinstance(other, self.__class__): 
            return False
        return self.plant_id == other.plant_id

    def __repr__(self): 
        return f"{self.plant_id}"

    def tons_below(self, f: Family): 
        ton_list = [family.ST * prod_rate
            for family, prod_rate in zip(self.families, self.production_rv)
                if ((family in self.families) 
                    and (family < f) 
                    and not (family == f)
                )
        ]
        return sum(ton_list)


