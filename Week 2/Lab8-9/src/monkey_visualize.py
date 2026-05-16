import argparse
import collections
import itertools

import matplotlib.pyplot as plt

from monkey_classif import read_monkeys_from_csv
from utils import patch_color_int, VALID_OBS

# note that we slightly modified the scatter plot herefor convenience of use!
def scatter(input_csv:str, obs_a:str, obs_b:str):
    """Produce a scatterplot visualization from a CSV file.
    Arguments:
        - `input_csv`, a monkey data CSV file
        - `obs_a`, which observation to plot on the X-axis,
        - `obs_b`, which observation to plot on the Y-axis
    """
    assert obs_a in VALID_OBS, f'"{obs_a}" is an incorrect observation column name.'
    assert obs_b in VALID_OBS, f'"{obs_b}" is an incorrect observation column name.'
    # get the data as a dataframe
    df = read_monkeys_from_csv(input_csv, strict=True)
    # add columns for color hue support
    df = patch_color_int(df)

    # we'll map species to integers 0 ... n in order to produce a legend
    species_to_idx = collections.defaultdict(itertools.count().__next__)
    # grab only the columns we need
    X, Y, labels = df[obs_a], df[obs_b], df["species"].apply(species_to_idx.__getitem__)

    # produce the scatter plot & legend, then show the image
    fig, ax = plt.subplots()
    sct = ax.scatter(X, Y, c=labels)
    lgd = ax.legend(
        sct.legend_elements()[0],
        sorted(species_to_idx, key=lambda s: species_to_idx[s]),
        title="Species")
    ax.add_artist(lgd)
    plt.xlabel(obs_a)
    plt.ylabel(obs_b)

    plt.show()
