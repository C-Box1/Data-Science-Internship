import argparse
import collections
from functools import reduce
from email.policy import strict

import pandas as pd
import numpy as np

from monkey_model import Monkey
from utils import check_hexacolor, hexacolor_to_int, euclidean_distance, get_cli_args, VALID_OBS, patch_color_int


def read_monkeys_from_csv(csv_filepath:str, strict:bool=False) -> pd.DataFrame:
	"""Read a monkey data from a CSV file and produce and return a dataframe"""
	df = pd.read_csv(csv_filepath)
     
	expected_columns = {"species", "size", "weight", "color"}
	if set(df.columns) != expected_columns:
		raise ValueError(f"invalid columns in CSV file. Expected {expected_columns}, got {df.columns}")

	if strict:
		if df.isnull().any().any() or (df == '').any().any():
			raise ValueError("Missing or empty values found (Strict Mode)")

	df["species"] = df["species"].fillna("")
	df = df[df["size"].notna() & df["weight"].notna() & df["color"].notna()]
	df = df[(df["size"] != '') & (df["weight"] != '') & (df["color"] != '')]

	df["size"] = pd.to_numeric(df["size"], errors='coerce')
	df["weight"] = pd.to_numeric(df["weight"], errors='coerce')
	df = df[(df["size"] > 0) & (df["weight"] > 0)]

	df = df[df["color"].apply(check_hexacolor)]
	df = df.dropna(subset=["size", "weight"])
	df = df.reset_index(drop = True)

	df["monkey"] = df.apply(lambda row: Monkey(row["weight"], row["size"], row["color"], species=row["species"]), axis = 1)
	df["fur_color_int"] = df["color"].apply(lambda c: hexacolor_to_int(c))
	df["bmi"] = df.apply(lambda row: row["monkey"].bmi, axis = 1)

	return df

def compute_knn(df:pd.DataFrame, k:int=5, columns:list=["fur_color_int", "bmi"])->pd.DataFrame:
    """update species information for a Monkey DataFrame using a KNN.
    Arguments:
        `df`: dataframe as obtained from `read_monkeys_from_csv`
        `k`: number of neighbors to consider
        `columns`: list of observations to consider. Are valid observations:
            - fur_color_int,
            - fur_color_int_r (for red hue of fur),
            - fur_color_int_g (for green hue of fur),
            - fur_color_int_b (for blue hue of fur),
            - weight
            - size
            - bmi
    Returns: the dataframe `df`, modified in-place
    """
    assert len(columns) >= 2, "Need at least 2 observation columns"
    assert all(c in VALID_OBS for c in columns), f"Invalid columns: {columns}"

    df = patch_color_int(df)

    # Step 1 — separate using filter instead of boolean indexing
    # filter returns only rows where species is not empty
    all_rows = [row for _, row in df.iterrows()]  # convert df to list of rows
    labelled   = list(filter(lambda row: row["species"] != "", all_rows))
    unlabelled = list(filter(lambda row: row["species"] == "", all_rows))

    # Step 2 — function that classifies ONE monkey using the current labelled list
    def classify_one(labelled_list, unlabelled_row):
        """Takes current labelled list + one unlabelled monkey, returns updated labelled list"""
        
        # get coordinates of the unlabelled monkey
        coords = [unlabelled_row[col] for col in columns]
        
        # sort labelled monkeys by distance to this monkey
        # sorted() uses a key function — no for loop needed
        sorted_neighbours = sorted(
            labelled_list,
            key=lambda labelled_row: euclidean_distance(
                coords,
                [labelled_row[col] for col in columns]
            )
        )
        
        # take K nearest and get majority vote
        k_nearest = sorted_neighbours[:k]
        predicted_species = collections.Counter(
            row["species"] for row in k_nearest
        ).most_common(1)[0][0]
        
        # update the dataframe
        df.at[unlabelled_row.name, "species"] = predicted_species
        df.at[unlabelled_row.name, "monkey"].species = predicted_species
        
        # return updated labelled list with this monkey added
        updated_row = df.loc[unlabelled_row.name]
        return labelled_list + [updated_row]

    # Step 3 — reduce over unlabelled monkeys
    # starts with labelled as accumulator, classifies one by one
    reduce(classify_one, unlabelled, labelled)

    return df


def save_to_csv(dataframe:pd.DataFrame, csv_filename:str):
    """Save monkey dataframe to CSV file"""
    dataframe.drop(columns=["monkey", "fur_color_int", "bmi"]).to_csv(csv_filename, index=False)


def main():
    args = get_cli_args()
    if args.command == "knn":
        df = read_monkeys_from_csv(args.input_csv)
        df = compute_knn(df, k=args.k, columns=args.obs)
        save_to_csv(df, args.output_csv)
    elif args.command == "visualize":
        from monkey_visualize import scatter
        scatter(args.input_csv, args.obs_a, args.obs_b)
    else:
        # this should be dead code.
        raise RuntimeError("invalid command name")


# main entry point
if __name__ == "__main__":
    main()
