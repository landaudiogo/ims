import functools

from typing import List, Optional
from dataclasses import dataclass
from scipy.optimize import fsolve
from statistics import NormalDist


normdist = NormalDist(mu=0, sigma=1)


class Family:


    def __init__(
        self,
        family_id: str,
        daily_demand: List[int],
        daily_sigma: List[int],
        dp: int,
        lt: int,
        tfr: int,
        cfr: int,
        ind_cost: int,
        fr: Optional[int] = None,
    ): 
        self.family_id = family_id
        self.daily_demand = daily_demand
        self.daily_sigma = daily_sigma
        self.dp = int(dp)
        self.lt = int(lt)
        self.tfr = int(tfr*100)
        self.cfr = int(cfr*100)
        self.ind_cost = ind_cost
        self.fr = int(cfr*100)
        self.cycles = []

    def calculate_cycles(self): 
        start_day = 1
        while start_day <= 365: 
            cycle = Cycle()
            self.cycles.append(cycle)
            cycle.calculate_SC(self.daily_demand, start_day, self.lt)
            cycle.calculate_sigma(self.daily_sigma, start_day, self.lt)
            cycle.calculate_BKG(self.fr)
            cycle.calculate_SS()
            print(self.family_id, cycle.SC, cycle.SS)
            start_day += self.lt + self.dp

class Cycle: 

    def __init__(self): 
        self.SC = None
        self.sigma = None
        self.BKG = None
        self.SS = None
        pass

    def calculate_SC(self, daily_demand, start_day, lt): 
        self.SC = sum(daily_demand[start_day-1: start_day-1+lt])

    def calculate_sigma(self, daily_sigma, start_day, lt): 
        self.sigma = functools.reduce(
            lambda acc, val: acc+val**2, 
            daily_sigma[start_day-1: start_day-1+lt], 0
        )**(1/2)

    def calculate_BKG(self, fr): 
        self.BKG = (1 - fr)*(self.SC)

    def calculate_SS(self): 
        self.SS = fsolve(
            self.solve_for_ss, 
            1, 
            args=tuple([self.sigma, self.BKG]),
        )[0]

    @staticmethod
    def solve_for_ss(ss, sigma, bkg):
        return - ss*(1 - normdist.cdf(ss/sigma)) + sigma*normdist.pdf(ss/sigma) - bkg


