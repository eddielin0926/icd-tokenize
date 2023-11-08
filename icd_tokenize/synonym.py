import os
import time

import pandas as pd
from rich.console import Console


class Synonym(dict):
    def __init__(self, dir_path: str = None) -> None:
        if dir_path is None:
            dir_path = os.path.join(os.path.dirname(__file__), "data")

        synonym_file = os.path.join(dir_path, "synonym.csv")
        df = pd.read_csv(synonym_file)
        for index, row in df.iterrows():
            icd = row["ICD1_Iris"]
            synonyms = row["中文診斷"]
            self[synonyms] = icd


def generate_synonym(icd_file: str = None):
    if icd_file is None:
        icd_file = os.path.join(
            os.path.dirname(__file__), "data", "中文字典_1100712_提供張老師_自定義字典.xlsx"
        )
    if not os.path.exists(icd_file):
        raise ValueError(f"File '{icd_file}' doesn't exist.")

    output_dir = os.path.join(os.path.dirname(__file__), "data")

    # Create rich console
    console = Console()

    # Start process timing
    start_time = time.time()

    # Read standard icd dictionary
    icd_df = pd.read_excel(icd_file)
    icd_df = icd_df[["ICD1_Iris", "中文診斷"]]
    icd_df["中文診斷"] = icd_df["中文診斷"].str.normalize("NFKC")
    icd_df = icd_df[icd_df.duplicated(subset=["ICD1_Iris"], keep=False)]
    icd_df = icd_df.sort_values(["ICD1_Iris"])
    icd_df.to_csv(os.path.join(output_dir, "synonym.csv"), index=False)

    # Stop process timing
    end_time = time.time()

    # Print process information
    console.print(f'Write into file: [cyan bold]{os.path.join(output_dir, "icd.csv")}[/]')
    console.print(f"Elapsed time:\t [green bold]{round((end_time - start_time), 3)}s[/]")
