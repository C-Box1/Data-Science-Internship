import argparse
import math
import re

import pandas as pd

VALID_OBS = {"fur_color_int", "fur_color_int_r", "fur_color_int_g", "fur_color_int_b", "weight", "size", "bmi"}

def check_hexacolor(hexacolor:str, _RE_HEXACOLOR:re.Pattern=re.compile(r"#[0-9A-Fa-f]{6}"))->bool:
    """Verify that hexacolor is a well formed str (e.g. #123456)"""
    return bool(re.fullmatch(_RE_HEXACOLOR, hexacolor))

def hexacolor_to_int(hexacolor_str:str, color_spec:str='rgb')->int:
    """Converts hexadecimal color representation to int.
    Arguments:
        `hexacolor_str`: the string to convert
        `color_spec`: a color scheme specification: "rgb" (to extract all hues),
        "r", "g", or "b" to extract red, green or blue only
    """
    if color_spec == 'rgb':
        return int(hexacolor_str[1:], 16)
    elif color_spec == 'r':
        return int(hexacolor_str[1:3], 16)
    elif color_spec == 'g':
        return int(hexacolor_str[3:5], 16)
    elif color_spec == 'b':
        return int(hexacolor_str[5:], 16)
    else:
        raise ValueError(f"Incorrect color specifier {color_spec}")

def patch_color_int(df:pd.DataFrame)->pd.DataFrame:
    """Adds columns to dataframe for color hues"""
    def make_col(c):
        df[f"fur_color_int_{c}"] = df["color"].apply(lambda h: hexacolor_to_int(h, color_spec=c))
    _ = list(map(make_col, "rgb"))
    return df

def euclidean_distance(coords_a:list, coords_b:list)->float:
    """Computes Euclidean distance for two points represented by `coords_a` and `coord_b`"""
    if len(coords_a) != len(coords_b):
        raise ValueError("Items have different numbers of coordinates.")
    return math.sqrt(sum((a  - b) ** 2 for a, b in zip(coords_a, coords_b)))

def get_cli_args()->argparse.Namespace:
    """Get command line arguments"""
    parser = argparse.ArgumentParser(description="Monkey KNN")
    # using the `dest` keyword, we can keep track of which subparser was used
    subparsers = parser.add_subparsers(help='sub-command', dest='command')

    # add CL args for knn
    parser_knn = subparsers.add_parser("knn", help="perform a KNN labelling over partially annotated monkey data")
    parser_knn.add_argument("input_csv", type=str, help="path to CSV input data file")
    parser_knn.add_argument("output_csv", type=str, help="path where to save computation results")
    parser_knn.add_argument("--k", type=int, default=5, help="number of neighbors to consider")
    parser_knn.add_argument("--obs", nargs="+", default=["bmi", "fur_color_int"], choices=VALID_OBS, help="observations to consider")

    # add CL args for viz
    parser_viz = subparsers.add_parser("visualize", help="perform a scatterplot visualization over fully annotated monkey data")
    parser_viz.add_argument("input_csv", type=str, help="path to CSV input data file")
    parser_viz.add_argument("obs_a", type=str, choices=VALID_OBS, help="observation for X-axis in scatter plot")
    parser_viz.add_argument("obs_b", type=str, choices=VALID_OBS, help="observation for Y-axis in scatter plot")

    return parser.parse_args()
