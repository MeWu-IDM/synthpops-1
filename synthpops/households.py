'''
Functions for generating households
'''

import sciris as sc
import numpy as np
from collections import Counter
from .config import logger as log, checkmem
from . import sampling as spsamp


def generate_household_sizes_from_fixed_pop_size(N, hh_size_distr):
    """
    Given a number of people and a household size distribution, generate the number of homes of each size needed to place everyone in a household.

    Args:
        N      (int)         : The number of people in the population.
        hh_size_distr (dict) : The distribution of household sizes.

    Returns:
        An array with the count of households of size s at index s-1.
    """

    # Quickly produce number of expected households for a population of size N
    ss = np.sum([hh_size_distr[s] * s for s in hh_size_distr])
    f = N / np.round(ss, 1)
    hh_sizes = np.zeros(len(hh_size_distr))

    for s in hh_size_distr:
        hh_sizes[s-1] = int(hh_size_distr[s] * f)
    N_gen = np.sum([hh_sizes[s-1] * s for s in hh_size_distr], dtype=int)

    # Check what population size was created from the drawn count of household sizes
    people_to_add_or_remove = N_gen - N

    # did not create household sizes to match or exceed the population size so add count for households needed
    hh_size_keys = [k for k in hh_size_distr]
    hh_size_distr_array = [hh_size_distr[k] for k in hh_size_keys]
    if people_to_add_or_remove < 0:

        people_to_add = -people_to_add_or_remove
        while people_to_add > 0:
            new_household_size = np.random.choice(hh_size_keys, p=hh_size_distr_array)

            if new_household_size > people_to_add:
                new_household_size = people_to_add
            people_to_add -= new_household_size

            hh_sizes[new_household_size-1] += 1

    # created households that result in too many people
    elif people_to_add_or_remove > 0:
        people_to_remove = people_to_add_or_remove
        while people_to_remove > 0:

            new_household_size_to_remove = np.random.choice(hh_size_keys, p=hh_size_distr_array)
            if new_household_size_to_remove > people_to_remove:
                new_household_size_to_remove = people_to_remove

            people_to_remove -= new_household_size_to_remove
            hh_sizes[new_household_size_to_remove-1] -= 1

    hh_sizes = hh_sizes.astype(int)
    return hh_sizes


def generate_household_head_age_by_size(hha_by_size_counts, hha_brackets, hh_size, single_year_age_distr):
    """
    Generate the age of the head of the household, also known as the reference person of the household,
    conditional on the size of the household.

    Args:
        hha_by_size_counts (matrix)  : A matrix in which each row contains the age distribution of the reference person for household size s at index s-1.
        hha_brackets (dict)          : The age brackets for the heads of household.
        hh_size (int)                : The household size.
        single_year_age_distr (dict) : The age distribution.

    Returns:
        Age of the head of the household or reference person.
    """
    distr = hha_by_size_counts[hh_size-1, :]
    b = spsamp.sample_single_arr(distr)
    hha = spsamp.sample_from_range(single_year_age_distr, hha_brackets[b][0], hha_brackets[b][-1])

    return hha


def generate_living_alone(hh_sizes, hha_by_size_counts, hha_brackets, single_year_age_distr):
    """
    Generate the ages of those living alone.

    Args:
        hh_sizes (array)             : The count of household size s at index s-1.
        hha_by_size_counts (matrix)  : A matrix in which each row contains the age distribution of the reference person for household size s at index s-1.
        hha_brackets (dict)          : The age brackets for the heads of household.
        single_year_age_distr (dict) : The age distribution.

    Returns:
        An array of households of size 1 where each household is a row and the value in the row is the age of the household member.
    """

    size = 1
    homes = np.zeros((hh_sizes[size-1], 1), dtype=int)

    for h in range(hh_sizes[size-1]):
        hha = generate_household_head_age_by_size(hha_by_size_counts, hha_brackets, size, single_year_age_distr)
        homes[h][0] = int(hha)

    return homes


def assign_uids_by_homes(homes, id_len=16, use_int=True):
    """
    Assign IDs to everyone in order by their households.

    Args:
        homes (array)  : The generated synthetic ages of household members.
        id_len (int)   : The length of the UID.
        use_int (bool) : If True, use ints for the uids of individuals; otherwise use strings of length 'id_len'.

    Returns:
        A copy of the generated households with IDs in place of ages, and a dictionary mapping ID to age.
    """
    age_by_uid_dic = dict()
    homes_by_uids = []

    for h, home in enumerate(homes):

        home_ids = []
        for a in home:
            if use_int:
                uid = len(age_by_uid_dic)
            else:
                uid = sc.uuid(length=id_len)
            age_by_uid_dic[uid] = a
            home_ids.append(uid)

        homes_by_uids.append(home_ids)

    return homes_by_uids, age_by_uid_dic


def generate_age_count(n, age_distr):
    """
    Generate a stochastic count of people for each age given the age
    distribution (age_distr) and number of people to generate (n).

    Args:
        n (int)                        : number of people to generate
        age_distr (list or np.ndarray) : single year age distribution

    Returns:
        dict: A dictionary with the count of people to generate for each age
        given an age distribution and the number of people to generate.
    """
    age_range = np.arange(0, len(age_distr))
    chosen = np.random.choice(age_range, size=n, p=age_distr)
    age_count = Counter(chosen)
    age_count = sc.mergedicts(dict.fromkeys(age_range, 0), age_count)
    return age_count


def generate_living_alone_method_2(hh_sizes, hha_by_size, hha_brackets, age_count):
    """
    Generate the ages of those living alone.

    Args:
        hh_sizes (array)     : The count of household size s at index s-1.
        hha_by_size (matrix) : A matrix in which each row contains the age distribution of the reference person for household size s at index s-1.
        hha_brackets (dict)  : The age brackets for the heads of household.
        age_distr (dict)     : The age distribution.

    Returns:
        An array of households of size 1 where each household is a row and the
        value in the row is the age of the household member.
    """
    distr = hha_by_size[0, :]
    distr = distr / np.sum(distr)

    h1_count = hh_sizes[0]
    hha_b = np.random.choice(range(len(distr)), size=h1_count, p=distr)

    hha_b_count = Counter(hha_b)
    hha_living_alone = []
    for hha_bi in hha_brackets:
        possible_hha_bi_ages = []
        for a in hha_brackets[hha_bi]:
            possible_hha_bi_ages.extend([a] * age_count[a])
        np.random.shuffle(possible_hha_bi_ages)
        chosen_hha = possible_hha_bi_ages[0:hha_b_count[hha_bi]]
        hha_living_alone.extend(chosen_hha)
    np.random.shuffle(hha_living_alone)

    homes = np.array(hha_living_alone).astype(int).reshape((len(hha_living_alone), 1))
    return homes


def generate_larger_household_sizes(hh_sizes):
    """
    Create a list of the households larger than 1 in random order so that as
    individuals are placed by age into homes running out of specific ages is not
    systemically an issue for any given household size unless certain sizes
    greatly outnumber households of other sizes.

    Args:
        hh_sizes (array) : The count of household size s at index s-1.

    Returns:
        Np.array: An array of household sizes to be generated and place people
        into households.
    """
    larger_hh_size_array = []
    for hs in range(2, len(hh_sizes) + 1):
        larger_hh_size_array.extend([hs] * hh_sizes[hs - 1])
    larger_hh_size_array = np.array(larger_hh_size_array)
    np.random.shuffle(larger_hh_size_array)
    return larger_hh_size_array


def generate_larger_households_head_ages(larger_hh_size_array, hha_by_size, hha_brackets, ages_left_to_assign):
    """
    Generate the ages of the heads of households for households larger than 2.
    """
    larger_hha_chosen = []

    # go through every household and choose the head age
    for nh, hs in enumerate(larger_hh_size_array):
        hs_distr = hha_by_size[hs - 1, :]
        hbi = spsamp.fast_choice(hs_distr)
        hbi_distr = np.array([ages_left_to_assign[a] for a in hha_brackets[hbi]])

        while sum(hbi_distr) == 0:
            hbi = spsamp.fast_choice(hs_distr)
            hbi_distr = np.array([ages_left_to_assign[a] for a in hha_brackets[hbi]])

        hha = hha_brackets[hbi][spsamp.fast_choice(hbi_distr)]
        ages_left_to_assign[hha] -= 1

        larger_hha_chosen.append(hha)

    return larger_hha_chosen, ages_left_to_assign


def generate_larger_households_method_2(larger_hh_size_array, larger_hha_chosen, hha_brackets, cm_age_brackets, cm_age_by_brackets_dic, household_matrix, ages_left_to_assign, homes_dic):
    """
    Assign people to households larger than one person (excluding special
    residences like long term care facilities or agricultural workers living in
    shared residential quarters.

    Args:
        hh_sizes (array)              : The count of household size s at index s-1.
        hha_by_size (matrix)          : A matrix in which each row contains the age distribution of the reference person for household size s at index s-1.
        hha_brackets (dict)           : The age brackets for the heads of household.
        cm_age_brackets (dict)        : The age brackets for the contact matrix.
        cm_age_by_brackets_dic (dict) : A dictionary mapping age to the age bracket range it falls within.
        household_matrix (dict)       : The age-specific contact matrix for the household ontact setting.
        larger_homes_age_count (dict) : Age count of people left to place in households larger than one person.

    Returns:
        dict: A dictionary of households by age indexed by household size.
    """

    # go through every household and assign the ages of the other household members from those left to place
    for nh, hs in enumerate(larger_hh_size_array):

        hha = larger_hha_chosen[nh]
        b = cm_age_by_brackets_dic[hha]

        home = np.zeros(hs)
        home[0] = hha

        for nj in range(1, hs):

            # can no longer place anyone in households where b is the age bracket of the head since those people are no longer available
            if np.sum(household_matrix[b, :]) == 0:
                break

            bi = spsamp.fast_choice(household_matrix[b, :])

            a_prob = np.array([ages_left_to_assign[a] for a in cm_age_brackets[bi]])
            if np.sum(a_prob) == 0:  # must check if all zeros since sp.fast_choice will not check
                household_matrix[:, bi] = 0  # turn off this part of the matrix

            # entire matrix has been turned off, can no longer select anyone
            if np.sum(household_matrix) == 0:
                break

            while np.sum(a_prob) == 0:  # must check if all zeros since sp.fast_choice will not check
                bi = spsamp.fast_choice(household_matrix[b, :])
                a_prob = np.array([ages_left_to_assign[a] for a in cm_age_brackets[bi]])

                if np.sum(a_prob) == 0:  # must check if all zeros sine sp.fast_choice will not check
                    household_matrix[:, bi] = 0

            aj = cm_age_brackets[bi][spsamp.fast_choice(a_prob)]
            ages_left_to_assign[aj] -= 1

            home[nj] = aj
        homes_dic[hs].append(home)

    for hs in homes_dic:
        homes_dic[hs] = np.array(homes_dic[hs]).astype(int)

    assert sum(ages_left_to_assign.values()) == 0, 'Check failed: generating larger households method 2.'  # at this point everyone should have been placed into a home
    return homes_dic, ages_left_to_assign


def get_all_households(homes_dic):
    """
    Get all households in a list, randomly assorted.

    Args:
        homes_dic (dict): A dictionary of households by age indexed by household size

    Returns:
        list: A random ordering of households with the ages of the individuals.
    """
    homes = []
    for hs in homes_dic:
        homes.extend(homes_dic[hs])

    np.random.shuffle(homes)
    return homes