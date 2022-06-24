import functools

from typing import List, Optional
from dataclasses import dataclass
from scipy.optimize import fsolve
from statistics import NormalDist

from exc import MissingContext

normdist = NormalDist(mu=0, sigma=1)


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
        self.__fr = None
        self.cycles = []
        self.set_cycles()

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
        )

    @staticmethod
    def solve_for_ss_and_bkg(xv, sigma, sc, fr):
        global normdist
        if sigma == 0: 
            return (0, 0)
        return (
            (xv[0] + sc)/(xv[0] + sc + xv[1]) - fr,
            (- xv[0]*(1 - normdist.cdf(xv[0]/sigma)) + sigma*normdist.pdf(xv[0]/sigma) - xv[1])
        )
        return - ss*(1 - normdist.cdf(ss/sigma)) + sigma*normdist.pdf(ss/sigma) - bkg


class Plant: 


    def __init__(
        self, plant_id, capacity, families, production_rv
    ):
        self.plant_id = plant_id
        self.capacity = capacity
        self.families = families
        self.production_rv = production_rv
