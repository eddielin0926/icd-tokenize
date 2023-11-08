import argparse
import os

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import track

from icd_tokenize.synonym import Synonym


class ICD:
    def __init__(self, dir_path: str = None) -> None:
        if dir_path is None:
            dir_path = os.path.join(os.path.dirname(__file__), "data")

        # diagnosis
        diagnosis_file = os.path.join(dir_path, "icd.csv")
        df = pd.read_csv(diagnosis_file)
        self.diagnosis = df["diagnosis"].to_list()

        # synonyms
        self.synonyms = Synonym()

    def generate(icd_excel: str = None, data_dir: str = None, output_dir: str = None):
        """Generate icd.csv from icd_excel and data_dir."""
        if icd_excel is None:
            icd_excel = os.path.join(
                os.path.dirname(__file__), "data", "中文字典_1100712_提供張老師_自定義字典.xlsx"
            )
        if not os.path.exists(icd_excel):
            raise ValueError(f"File '{icd_excel}' doesn't exist.")
        if not os.path.exists(data_dir):
            raise ValueError(f"Directory '{data_dir}' doesn't exist.")
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "data")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create rich console
        console = Console()

        # Read standard icd dictionary
        icd_df = pd.read_excel(icd_excel)
        icd_df = icd_df.replace(np.nan, "", regex=True)  # replace nan with empty string
        icd_df["中文診斷"] = icd_df["中文診斷"].str.normalize("NFKC")
        icd_df.columns = [
            "diagnosis",
            "note",
            "ICD1",
            "ICD2",
            "ICD3",
            "ICD4",
            "ICD5",
        ]
        icd_df = icd_df.sort_values(["diagnosis"])
        icd_df.to_csv(os.path.join(output_dir, "original-icd.csv"), index=False)
        console.print(
            f'Write into file:\t [cyan bold]{os.path.join(output_dir, "original-icd.csv")}[/]'
        )

        covid_df = pd.read_csv(os.path.join(output_dir, "covid.csv"))
        covid_df["ICD1"] = ["J128"] * len(covid_df)

        syn_df = icd_df[["ICD1", "diagnosis"]]
        syn_df = syn_df[syn_df.duplicated(subset=["ICD1"], keep=False)]
        syn_df = pd.concat([syn_df, covid_df], ignore_index=True)
        syn_df = syn_df.sort_values(["ICD1"])
        syn_df.to_csv(os.path.join(output_dir, "synonym.csv"), index=False)
        console.print(f'Write into file:\t [cyan bold]{os.path.join(output_dir, "synonym.csv")}[/]')

        icd_set = {}
        for _, row in icd_df.iterrows():
            icd_set[row["diagnosis"]] = True

        non_icd_set = {}
        for file in os.listdir(data_dir):
            if "(00000)" in file:
                continue
            df = pd.read_excel(os.path.join(data_dir, file), header=1)
            df = df.replace(np.nan, "", regex=True)  # replace nan with empty string

            df = df.iloc[:, 23:43]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
            for col in df.columns:
                df[col] = df[col].str.normalize("NFKC")
            df.columns = df.columns.str.rstrip(".1")

            for _, row in track(df.iterrows(), total=len(df), description=f"[green]{file} "):
                for catalog in ["甲", "乙", "丙", "丁", "其他"]:
                    for i in ["", "2", "3", "4"]:
                        key = row[f"{catalog}{i}"]
                        if key != "" and "?" not in key:
                            if key not in icd_set:
                                icd_set[key] = True
                                non_icd_set[key] = True

        # Remove certain icd from final result
        exclude_icd_df = pd.read_csv(os.path.join(output_dir, "exclude-icd.csv"))
        for key in exclude_icd_df["diagnosis"]:
            if key in icd_set:
                icd_set[key] = False
            else:
                console.print(f"Warning: '{key}' doesn't exist in the ICD.")

        # Dump existed diagnosis results which are not in the icd dictionary
        df_non_icd = pd.DataFrame(list(non_icd_set.keys()), columns=["diagnosis"])
        df_non_icd = df_non_icd.sort_values(["diagnosis"])
        df_non_icd.to_csv(os.path.join(output_dir, "non-verified-icd.csv"), index=False)
        console.print(
            f'Write into file:\t [cyan bold]{os.path.join(output_dir, "non-verified-icd.csv")}[/]'
        )

        # Dump final result
        df_result = pd.DataFrame(
            [i for i in list(icd_set.keys()) if icd_set[i]], columns=["diagnosis"]
        )
        df_result = df_result.sort_values(["diagnosis"])
        df_result.to_csv(os.path.join(output_dir, "icd.csv"), index=False)
        console.print(f'Write into file:\t [cyan bold]{os.path.join(output_dir, "icd.csv")}[/]')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--icd", help="icd file path")
    parser.add_argument("-o", "--output", help="output directory")
    parser.add_argument("data", help="data directory", default="data")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"Directory '{args.data}' doesn't exist.")

    ICD.generate(data_dir=args.data)
