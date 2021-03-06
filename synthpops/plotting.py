"""
This module plots the age-specific contact matrix in different settings.
"""
import os
import numpy as np
import matplotlib as mplt
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from collections import Counter
from . import config as cfg
from . import base as spb
from . import data_distributions as spdd


# Pretty fonts
try:
    fontstyle = 'Roboto Condensed'
    mplt.rcParams['font.family'] = fontstyle
except:
    mplt.rcParams['font.family'] = 'Roboto'
mplt.rcParams['font.size'] = 16

try:
    import cmasher
    default_colormap = 'cmr.freeze_r'
except:
    print('Note: cmasher import failed; defaulting to regular colormap')
    default_colormap = 'bone_r'


__all__ = ['calculate_contact_matrix', 'plot_contacts']


def calculate_contact_matrix(population, density_or_frequency='density', setting_code='H'):
    """
    Calculate the symmetric age-specific contact matrix from the connections
    for all people in the population. density_or_frequency sets the type of
    contact matrix calculated.

    When density_or_frequency is set to 'frequency' each person is assumed to
    have a fixed amount of contact with others they are connected to in a
    setting so each person will split their contact amount equally among their
    connections. This means that if a person has links to 4 other individuals
    then 1/4 will be added to the matrix element matrix[age_i][age_j] for each
    link, where age_i is the age of the individual and age_j is the age of the
    contact. This follows the mass action principle such that increased density
    or number of people a person is in contact with leads to decreased per-link
    or connection contact rate.

    When density_or_frequency is set to 'density' the amount of contact each
    person has with others scales with the number of people they are connected
    to. This means that a person with connections to 4 individuals has a higher
    total contact rate than a person with connection to 3 individuals. For this
    definition if a person has links to 4 other individuals then 1 will be
    added to the matrix element matrix[age_i][age_j] for each contact. This
    follows the 'pseudo'mass action principle such that the per-link or
    connection contact rate is constant.

    Args:
        population (dict)          : A dictionary of a population with attributes.
        density_or_frequency (str) : option for the type of contact matrix calculated.
        setting_code (str)         : name of the physial contact setting: H for households, S for schools, W for workplaces, C for community or other, and 'lTCF' for long term care facilities

    Returns:
        Symmetric age specific contact matrix.

    """
    uids = population.keys()
    uids = [uid for uid in uids]

    num_ages = 101

    M = np.zeros((num_ages, num_ages))

    for n, uid in enumerate(uids):
        age = population[uid]['age']
        contact_ages = [population[c]['age'] for c in population[uid]['contacts'][setting_code]]
        contact_ages = np.array([int(a) for a in contact_ages])

        if len(contact_ages) > 0:
            if density_or_frequency == 'frequency':
                for ca in contact_ages:
                    M[age, ca] += 1.0 / len(contact_ages)
            elif density_or_frequency == 'density':
                for ca in contact_ages:
                    M[age, ca] += 1.0
    return M


def plot_contact_matrix(matrix, age_count, aggregate_age_count, age_brackets, age_by_brackets_dic,
                        setting_code='H', density_or_frequency='density', logcolors_flag=False,
                        aggregate_flag=True, cmap=default_colormap, fontsize=16, rotation=50,
                        title_prefix=None, fig=None, ax=None):
    """
    Plots the age specific contact matrix where the matrix element matrix_ij is the contact rate or frequency
    for the average individual in age group i with all of their contacts in age group j. Can either be density
    or frequency definition, as well as a single year age contact matrix or a contact matrix for aggregated
    age brackets.

    Args:
        matrix (np.array)                : symmetric contact matrix, element ij is the contact for an average individual in age group i with all of their contacts in age group j
        age_count (dict)                 : dictionary with the count of individuals in the population for each age
        aggregate_age_count (dict)       : dictionary with the count of individuals in the population in each age bracket
        age_brackets (dict)              : dictionary mapping age bracket keys to age bracket range
        age_by_brackets_dic (dict)       : dictionary mapping age to the age bracket range it falls in
        setting_code (str)               : name of the physial contact setting: H for households, S for schools, W for workplaces, C for community or other
        density_or_frequency (str)       : If 'density', then each contact counts for 1/(group size -1) of a person's contact in a group, elif 'frequency' then count each contact. This means that more people in a group leads to higher rates of contact/exposure.
        logcolors_flag (bool)            : If True, plot heatmap in logscale
        aggregate_flag (bool)            : If True, plot the contact matrix for aggregate age brackets, else single year age contact matrix.
        cmap(str or matplotlib colormap) : colormap
        fontsize (int)                   : base font size
        rotation (int)                   : rotation for x axis labels
        title_prefix(str)                : optional title prefix for the figure
        fig (Figure)                     : if supplied, use this figure instead of generating one
        ax (Axes)                        : if supplied, use these axes instead of generating one

    Returns:
        A fig object.

    Note:
        For the long term care facilities you may want the age count and the aggregate age count to only consider those who live or work in long term care facilities because otherwise this will be the whole population wide average mixing in that setting

    """
    cmap = mplt.cm.get_cmap(cmap)

    if fig is None:
        fig = plt.figure(figsize=(10, 10), tight_layout=True)
    if ax is None:
        ax = [fig.add_subplot(1, 1, 1)]
    else:
        ax = [ax]
    cax = []
    cbar = []
    implot = []

    titles = {'H': 'Household', 'S': 'School', 'W': 'Work', 'LTCF': 'Long Term Care Facilities'}

    if aggregate_flag:
        aggregate_M = spb.get_aggregate_matrix(matrix, age_by_brackets_dic)
        asymmetric_M = spb.get_asymmetric_matrix(aggregate_M, aggregate_age_count)
    else:
        asymmetric_M = spb.get_asymmetric_matrix(matrix, age_count)

    if logcolors_flag:

        vbounds = {}
        if density_or_frequency == 'frequency':
            if aggregate_flag:
                vbounds['H'] = {'vmin': 1e-2, 'vmax': 1e-0}
                vbounds['S'] = {'vmin': 1e-3, 'vmax': 1e-0}
                vbounds['W'] = {'vmin': 1e-3, 'vmax': 1e-0}
                vbounds['LTCF'] = {'vmin': 1e-3, 'vmax': 1e-1}
            else:
                vbounds['H'] = {'vmin': 1e-3, 'vmax': 1e-1}
                vbounds['S'] = {'vmin': 1e-3, 'vmax': 1e-1}
                vbounds['W'] = {'vmin': 1e-3, 'vmax': 1e-1}
                vbounds['LTCF'] = {'vmin': 1e-3, 'vmax': 1e-0}

        elif density_or_frequency == 'density':
            if aggregate_flag:
                vbounds['H'] = {'vmin': 1e-2, 'vmax': 1e0}
                vbounds['S'] = {'vmin': 1e-2, 'vmax': 1e1}
                vbounds['W'] = {'vmin': 1e-2, 'vmax': 1e1}
                vbounds['LTCF'] = {'vmin': 1e-3, 'vmax': 1e-0}

            else:
                vbounds['H'] = {'vmin': 1e-2, 'vmax': 1e0}
                vbounds['S'] = {'vmin': 1e-2, 'vmax': 1e0}
                vbounds['W'] = {'vmin': 1e-2, 'vmax': 1e0}
                vbounds['LTCF'] = {'vmin': 1e-2, 'vmax': 1e-0}

        im = ax[0].imshow(asymmetric_M.T, origin='lower', interpolation='nearest', cmap=cmap, norm=LogNorm(vmin=vbounds[setting_code]['vmin'], vmax=vbounds[setting_code]['vmax']))

    else:

        im = ax[0].imshow(asymmetric_M.T, origin='lower', interpolation='nearest', cmap=cmap)

    implot.append(im)

    if fontsize > 20:
        rotation = 90

    for i in range(len(ax)):
        divider = make_axes_locatable(ax[i])
        cax.append(divider.new_horizontal(size="4%", pad=0.15))

        fig.add_axes(cax[i])
        cbar.append(fig.colorbar(implot[i], cax=cax[i]))
        cbar[i].ax.tick_params(axis='y', labelsize=fontsize + 4)
        if density_or_frequency == 'frequency':
            cbar[i].ax.set_ylabel('Frequency of Contacts', fontsize=fontsize + 2)
        else:
            cbar[i].ax.set_ylabel('Density of Contacts', fontsize=fontsize + 2)
        ax[i].tick_params(labelsize=fontsize + 2)
        ax[i].set_xlabel('Age', fontsize=fontsize + 6)
        ax[i].set_ylabel('Age of Contacts', fontsize=fontsize + 6)
        # ax[i].set_title(titles[setting_code] + ' Contact Patterns', fontsize=fontsize + 10)
        ax[i].set_title(
            (title_prefix if title_prefix is not None else '') + titles[setting_code] + ' Age Mixing', fontsize=fontsize + 10)

        if aggregate_flag:
            tick_labels = [str(age_brackets[b][0]) + '-' + str(age_brackets[b][-1]) for b in age_brackets]
            ax[i].set_xticks(np.arange(len(tick_labels)))
            ax[i].set_xticklabels(tick_labels, fontsize=fontsize)
            ax[i].set_xticklabels(tick_labels, fontsize=fontsize, rotation=rotation)
            ax[i].set_yticks(np.arange(len(tick_labels)))
            ax[i].set_yticklabels(tick_labels, fontsize=fontsize)
        else:
            ax[i].set_xticks(np.arange(0, len(age_count) + 1, 10))
            ax[i].set_yticks(np.arange(0, len(age_count) + 1, 10))

    return fig


def plot_contacts(population,
                  setting_code='H',
                  aggregate_flag=True,
                  logcolors_flag=True,
                  density_or_frequency='density',
                  cmap=default_colormap,
                  fontsize=16,
                  rotation=50,
                  title_prefix=None,
                  fig=None,
                  ax=None,
                  do_show=True):
    """
    Plot the age mixing matrix for a specific setting.

    TODO: rename setting_code to layer

    Args:
        population(dict)                 : population to be plotted, if None, code will generate it
        setting_code (str)               : name of the physial contact setting: H for households, S for schools, W for workplaces, C for community or other
        aggregate_flag (bool)            : If True, plot the contact matrix for aggregate age brackets, else single year age contact matrix.
        logcolors_flag (bool)            : If True, plot heatmap in logscale
        density_or_frequency (str)       : If 'density', then each contact counts for 1/(group size -1) of a person's contact in a group, elif 'frequency' then count each contact. This means that more people in a group leads to higher rates of contact/exposure.
        cmap(str or matplotlib colormap) : colormap
        fontsize (int)                   : base font size
        rotation (int)                   : rotation for x axis labels
        title_prefix(str)                : optional title prefix for the figure
        fig (Figure)                     : if supplied, use this figure instead of generating one
        ax (Axes)                        : if supplied, use these axes instead of generating one
        do_show (bool)                   : whether to show the plot

    Returns:
        A fig object.

    """
    datadir = cfg.datadir

    state_location = 'Washington'
    country_location = 'usa'

    age_brackets = spdd.get_census_age_brackets(datadir, state_location=state_location, country_location=country_location)
    age_by_brackets_dic = spb.get_age_by_brackets_dic(age_brackets)

    ages = []
    # if setting_code == 'LTCF':
    #     ltcf_ages = []

    for uid in population:
        ages.append(population[uid]['age'])
        # if setting_code == 'LTCF':
        #     if population[uid]['snf_res'] or population[uid]['snf_staff']:
        #         ltcf_ages.append(population[uid]['age'])

    age_count = Counter(ages)
    aggregate_age_count = spb.get_aggregate_ages(age_count, age_by_brackets_dic)

    # if setting_code == 'LTCF':
    #     ltcf_age_count = Counter(ltcf_ages)
    #     aggregate_ltcf_age_count = sp.get_aggregate_ages(ltcf_age_count, age_by_brackets_dic)

    matrix = calculate_contact_matrix(population, density_or_frequency, setting_code)

    # if setting_code == 'LTCF':
    #     fig = sp.plot_contact_frequency(matrix, ltcf_age_count, aggregate_ltcf_age_count, age_brackets, age_by_brackets_dic,
    #                                     setting_code, density_or_frequency, logcolors_flag, aggregate_flag, cmap, fontsize, rotation)
    # else:
    #     fig = sp.plot_contact_frequency(matrix, age_count, aggregate_age_count, age_brackets, age_by_brackets_dic,
    #                                     setting_code, density_or_frequency, logcolors_flag, aggregate_flag, cmap, fontsize, rotation)

    fig = plot_contact_matrix(matrix, age_count, aggregate_age_count, age_brackets, age_by_brackets_dic,
                              setting_code, density_or_frequency, logcolors_flag, aggregate_flag, cmap, fontsize, rotation, title_prefix,
                              fig=fig, ax=ax)

    if do_show:
        plt.show()

    return fig


def plot_array(expected,
               generated=None,
               names=None,
               figdir=None,
               testprefix="test",
               do_show=True,
               do_save=False,
               expect_label='Expected',
               value_text=False,
               xlabels=None,
               xlabel_rotation=0,
               binned=True):
    """
    Plot histogram on a sorted array based by names. If names not provided the
    order will be used. If generate data is not provided, plot only the expected values.
    Note this can only be used with the limitation that data that has already been binned

    Args:
        expected        : Array of expected values
        generated       : Array of values generated using a model
        names           : names to display on x-axis, default is set to the indexes of data
        figdir          : directory to save the plot if provided
        testprefix      : used to prefix the title of the plot
        do_close        : close the plot immediately if set to True
        expect_label    : Label to show in the plot, default to "expected"
        value_text      : display the values on top of the bar if specified
        xlabel_rotation : rotation degree for x labels if specified
        binned          : default to True, if False, it will just plot a simple histogram for expected data

    Returns:
        None.

    Plot will be saved in datadir if given
    """
    fig, ax = plt.subplots(1, 1)
    # font = {
    #         'size': 14
    #         }
    # plt.rc('font', **font)
    mplt.rcParams['font.family'] = 'Roboto Condensed'
    title = testprefix if generated is None else f"Comparison for {testprefix}"
    ax.set_title(title)
    x = np.arange(len(expected))

    if not binned:
        ax.hist(expected, label=expect_label.title(), color='mediumseagreen')
    else:
        rect1 = ax.bar(x, expected, label=expect_label.title(), color='mediumseagreen')
        # ax.hist(x=names, histtype='bar', weights=expected, label=expect_label.title(), bins=bin, rwidth=1, color='#1a9ac0', align='left')
        if generated is not None:
            line, = ax.plot(x, generated, color='#236a54', markeredgecolor='white', marker='o', markersize=6, label='Generated')
            # arr = ax.hist(x=names, histtype='step', linewidth=3, weights=actual, label='Actual', bins=len(actual), rwidth=1, color='#ff957a', align='left')
        if value_text:
            autolabel(ax, rect1, 0, 5)
            if generated is not None:
                for j, v in enumerate(generated):
                    ax.text(j, v, str(round(v, 3)), fontsize=10, horizontalalignment='right', verticalalignment='top', color='#3f75a2')
        if names is not None:
            if isinstance(names, dict):
                xticks = sorted(names.keys())
                xticklabels = [names[k] for k in xticks]
            else:
                xticks = np.arange(len(names))
                xticklabels = names
            # plt.locator_params(axis='x', nbins=len(xticks))
            # if the labels are too many it will look crowded so we only show every 10 ticks
            if len(names) > 30:
                xticks = xticks[0::10]
                xticklabels = xticklabels[0::10]
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticklabels, rotation=xlabel_rotation)
            # ax.set_xlim(left=-1)
    leg = ax.legend(loc='upper right')
    leg.draw_frame(False)

    if do_save:
        if figdir:
            datadir = cfg.datadir
            figdir = os.path.join(datadir, 'figures')
            os.makedirs(figdir, exist_ok=True)
            plt.savefig(os.path.join(figdir, f"{testprefix}.png".replace('\n', '_')), format="png")
    if do_show:
        plt.show()
    # else:
    #     plt.close()
    return fig, ax


def autolabel(ax, rects, h_offset=0, v_offset=0.3):
    """
    Attach a text label above each bar in *rects*, displaying its height.

    Args:
        ax       : matplotlib.axes figure object
        rects    : matplotlib.container.BarContainer
        h_offset : The position x to place the text at.
        v_offset : The position y to place the text at.

    Returns:
        None.

    Set the annotation according to the input parameters
    """
    for rect in rects:
        height = rect.get_height()
        text = ax.annotate('{}'.format(round(height, 3)),
                           xy=(rect.get_x() + rect.get_width() / 2, height),
                           xytext=(h_offset, v_offset),
                           textcoords="offset points",
                           ha='center', va='bottom')
        text.set_fontsize(10)