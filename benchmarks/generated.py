import random
import numpy as np

def generate_random_alldiffs(n_vars, n_cons, p=0.5, seed=0):

    random.seed(seed)

    subsets = []
    for i in range(n_cons):
        idxes = [i for i in range(n_vars) if random.random() <= p]
        subsets.append(idxes)

    return {
        "n_vars": n_vars,
        "subsets": subsets,
    }

def generate_random_gcc(n_vars,n_cons, lb, ub, p=0.5, seed=0):

    random.seed(seed)

    subsets = []
    values = []
    counts = []

    for i in range(n_cons):
        idxes = [i for i in range(n_vars) if random.random() <= p]
        subsets.append(idxes)

        nb_counts = random.randint(1, len(idxes))
        chosen_values = random.sample(list(range(lb,ub+1)),k=nb_counts)
        values.append(chosen_values)

        chosen_counts = [1 for _ in range(nb_counts)]
        for _ in range(len(idxes) - nb_counts):
            chosen_counts[random.randint(0,nb_counts-1)] += 1
        counts.append(chosen_counts)

        # print(chosen_counts)

    return {
            "lb":lb, "ub":ub,"n_vars":n_vars,
        "subsets": subsets,
        "values": values,
        "counts": counts
    }

def generate_random_cumulatives(n_tasks, n_cons, lb, ub, p=0.5, seed=0):

    random.seed(seed)

    subsets = []
    durations = np.array([random.randint(5, 10) for _ in range(n_tasks)])
    demands = np.array([random.randint(1, 5) for _ in range(n_tasks)])

    capacities = []
    for i in range(n_cons):
        idxes = [i for i in range(n_tasks) if random.random() <= p]
        subsets.append(idxes)
        capacities.append(random.randint(max(demands[idxes]),10))


    return {
        "n_tasks": n_tasks,
        "lb":lb, "ub":ub,
        "subsets": subsets,
        "durations": durations,
        "demands": demands,
        "capacities": capacities,
    }

def generate_set_instance(n_cards, size_of_set=3, seed=0):

    n_values = size_of_set
    n_attr = size_of_set + 1

    rs = np.random.RandomState(seed)

    return {"cards": rs.randint(1,n_values+1, size=n_cards*n_attr).reshape(n_cards, n_attr),
            "size_of_set": size_of_set,}