"""
Test that the inter_grade_mixing parameter is being used for specific school
mixing types.

We expect inter_grade_mixing to be used when school_mixing_type equals
'age_clustered', and to be ignored when school_mixing_type is equal to either
'random' or 'age_and_class_clustered'.
"""

import os
import sciris as sc
import synthpops as sp
import numpy as np

# parameters to generate a test population
pars = dict(
        n                               = 20001,
        rand_seed                       = 123,
        max_contacts                    = None,

        with_industry_code              = 0,
        with_facilities                 = 1,
        with_non_teaching_staff         = 1,
        use_two_group_reduction         = 1,
        with_school_types               = 1,

        average_LTCF_degree             = 20,
        ltcf_staff_age_min              = 20,
        ltcf_staff_age_max              = 60,

        school_mixing_type              = 'age_clustered',
        average_class_size              = 20,
        inter_grade_mixing              = 0.1,
        teacher_age_min                 = 25,
        teacher_age_max                 = 75,
        staff_age_min                   = 20,
        staff_age_max                   = 75,

        average_student_teacher_ratio   = 20,
        average_teacher_teacher_degree  = 3,
        average_student_all_staff_ratio = 15,
        average_additional_staff_degree = 20,
)


def test_inter_grade_mixing(school_mixing_type='random'):
    """
    When school_mixing_type is 'age_clustered' then inter_grade_mixing should
    rewire a fraction of the edges between students in the same age or grade to
    be edges with any other student in the school.

    When school_mixing_type is 'random' or 'age_and_class_clustered',
    inter_grade_mixing has no effect.

    Args:
        school_mixing_type (str): The mixing type for schools, 'random', 'age_clustered', or 'age_and_class_clustered'.

    """
    sp.logger.info(f'Testing the effect of the parameter inter_grade_mixing for school_mixing_type: {school_mixing_type}')

    test_pars = sc.dcp(pars)
    test_pars['school_mixing_type'] = school_mixing_type

    pop_1 = sp.make_population(**test_pars)
    test_pars['inter_grade_mixing'] = 0.3
    pop_2 = sp.make_population(**test_pars)

    # make an adjacency matrix of edges between students
    adjm_1 = np.zeros((101, 101))
    adjm_2 = np.zeros((101, 101))

    student_ids = set()
    for i, person in pop_1.items():
        if person['sc_student']:
            student_ids.add(i)

    for ni, i in enumerate(student_ids):

        contacts_1 = pop_1[i]['contacts']['S']
        contacts_2 = pop_2[i]['contacts']['S']

        student_contacts_1 = list(set(contacts_1).intersection(student_ids))
        student_contacts_2 = list(set(contacts_2).intersection(student_ids))

        age_i = pop_1[i]['age']

        for nj, j in enumerate(student_contacts_1):
            age_j = pop_1[j]['age']
            adjm_1[age_i][age_j] += 1

        for nj, j in enumerate(student_contacts_2):
            age_j = pop_2[j]['age']
            adjm_2[age_i][age_j] += 1

    if school_mixing_type in ['random', 'age_and_class_clustered']:
        assert np.not_equal(adjm_1, adjm_2).sum() == 0, f"inter_grade_mixing parameter check failed. Different values for this parameter produced different results for school_mixing_type: {school_mixing_type}."

    elif school_mixing_type in ['age_clustered']:
        assert np.not_equal(adjm_1, adjm_2).sum() > 0, f"inter_grade_mixing parameter check failed. It produced the same results for different values of this parameter for school_mixing_type: {school_mixing_type}."


if __name__ == '__main__':

    sc.tic()
    test_inter_grade_mixing('random')
    test_inter_grade_mixing('age_clustered')
    test_inter_grade_mixing('age_and_class_clustered')

    sc.toc()
