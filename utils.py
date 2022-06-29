from functools import cmp_to_key

@cmp_to_key
def cmp_families(f1, f2): 
    if f1.revenue > f2.revenue: 
        return 1
    if f1.revenue == f2.revenue: 
        if f1.family_id <= f2.family_id: 
            return 1
        if f1.family_id > f2.family_id: 
            return -1
    if f1.revenue < f2.revenue: 
        return -1

@cmp_to_key
def cmp_plants(p1, p2): 
    return p1.plant_id > p1.plant_id
