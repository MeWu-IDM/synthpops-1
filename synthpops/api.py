"""
This module provides the layer for communicating with the agent-based model Covasim.
"""

import sciris as sc
import synthpops as sp
from . import config as cfg

# Put this here so it's accessible as sp.api.popsize_choices
popsize_choices = [5000,
                   10000,
                   20000,
                   50000,
                   100000,
                   120000,
                ]


def make_population(n=None, max_contacts=None, generate=None, with_industry_code=False, with_facilities=False,
                    use_two_group_reduction=True, average_LTCF_degree=20, rand_seed=None,
                    location=None, state_location=None, country_location=None, sheet_name = None):
    '''
    Make a full population network including both people (ages, sexes) and contacts using Seattle, Washington cached data.

    Args:
        n (int)                        : The number of people to create.
        max_contacts (dict)            : A dictionary for maximum number of contacts per layer: keys must be "S" (school) and/or "W" (work).
        generate (bool)                : If True, first look for cached population files and if those are not available, generate new population
        with_industry_code (bool)      : If True, assign industry codes for workplaces, currently only possible for cached files of populations in the US
        with_facilities (bool)         : If True, create long term care facilities
        use_two_group_reduction (bool) : If True, create long term care facilities with reduced contacts across both groups
        average_LTCF_degree (int)      : default average degree in long term care facilities
        state_location (string)   : name of the state the location is in
        country_location (string) : name of the country the location is in

    Returns:
        network (dict): A dictionary of the full population with ages and connections.

    '''

    if rand_seed is not None:
        sp.set_seed(rand_seed)

    default_n = 10000
    default_max_contacts = {'S': 20, 'W': 20}  # this can be anything but should be based on relevant average number of contacts for the population under study

    if n is None:
        n = default_n
    n = int(n)

    if n not in popsize_choices:
        if generate is False:
            choicestr = ', '.join([str(choice) for choice in popsize_choices])
            errormsg = f'If generate=False, number of people must be one of {choicestr}, not {n}'
            raise ValueError(errormsg)
        else:
            generate = True # If not found, generate

    # Default to False, unless LTCF are requested
    if generate is None:
        if with_facilities:
            generate = True
        else:
            generate = False

    max_contacts = sc.mergedicts(default_max_contacts, max_contacts)

    if country_location is None:
        # If no country is specified assume that defaults are used
        country_location = cfg.default_country
        state_location = cfg.default_state
        location = cfg.default_location
    else:
        # each country has a set of default values that are used, so get the defaults
        # load defaults for the country
        sp.config.set_location_defaults(country_location)

    # if country is specified, and state is not, we are using country level data to create a
    # network population. Set location to None
    if state_location is None:
        location = None

    sheet_name = cfg.default_sheet_name if sheet_name is None else sheer_name


    options_args = {'use_microstructure': True, 'use_industry_code': with_industry_code, 'use_long_term_care_facilities': with_facilities, 'use_two_group_reduction': use_two_group_reduction, 'average_LTCF_degree': average_LTCF_degree}
    network_distr_args = {'Npop': int(n)}

    # Heavy lift 1: make the contacts and their connections
    if not generate:
        # must read in from file, will fail if the data has not yet been generated
        population = sp.make_contacts(location=location, state_location=state_location, country_location=country_location, options_args=options_args, network_distr_args=network_distr_args)
    else:
        # make a new network on the fly
        if with_facilities and with_industry_code:
            errormsg = f'Requesting both long term care facilities and industries by code is not supported yet.'
            raise ValueError(errormsg)
        elif with_facilities:
            population = sp.generate_microstructure_with_facilities(sp.datadir, location=location, state_location=state_location, country_location=country_location, n=n, return_popdict=True, use_two_group_reduction=use_two_group_reduction, average_LTCF_degree=average_LTCF_degree)
        else:
            population = sp.generate_synthetic_population(n, sp.datadir, location=location, state_location=state_location, country_location=country_location, sheet_name=sheet_name, plot=False, return_popdict=True)

    # Semi-heavy-lift 2: trim them to the desired numbers
    population = sp.trim_contacts(population, trimmed_size_dic=max_contacts, use_clusters=False)

    # Change types
    for key,person in population.items():
        for layerkey in population[key]['contacts'].keys():
            population[key]['contacts'][layerkey] = list(population[key]['contacts'][layerkey])
    return population
