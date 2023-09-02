import os
import time
import pygtrie
import numpy as np
import pandas as pd
from rich.progress import track
from rich.console import Console


class ICD:
    def __init__(self, dir_path: str = None) -> None:
        if dir_path is None:
            dir_path = os.path.join(os.path.dirname(__file__), "data")

        # diagnosis
        diagnosis_file = os.path.join(dir_path, "icd.csv")
        df = pd.read_csv(diagnosis_file)
        self.diagnosis = df["diagnosis"].to_list()

        # synonyms
        synonyms_file = os.path.join(dir_path, "synonyms.txt")
        with open(synonyms_file, "r", encoding="utf-8") as f:
            self.synonyms = []
            for line in f.readlines():
                line = line.replace("\n", "")
                self.synonyms_list.append(line.split(","))


def generate_icd():
    data_path = os.path.join(os.path.dirname(__file__), "data")

    # Create rich console
    console = Console()

    # Start process timing
    start_time = time.time()

    # Read standard icd dictionary
    icd_df = pd.read_excel(os.path.join(data_path, "中文字典_1100712_提供張老師_自定義字典.xlsx"))
    icd_df = pd.DataFrame(
        icd_df["中文診斷"].str.normalize("NFKC").to_list(), columns=["diagnosis"]
    )
    icd_df = icd_df.sort_values(["diagnosis"])
    icd_df.to_csv(os.path.join(data_path, "original-icd.csv"), index=False)

    # Create icd trie
    icd_list = icd_df["diagnosis"].to_list()
    icd_trie = pygtrie.CharTrie()
    for icd in icd_list:
        icd_trie[icd] = True

    non_icd_list = []
    result_list = []
    result_trie = pygtrie.CharTrie()
    for file in os.listdir("./data"):
        df = pd.read_excel(os.path.join("data", file), header=1)
        df = df.drop("NO", axis=1)
        df = df.replace(np.nan, "", regex=True)  # replace nan with empty string

        df_result = df.iloc[:, 22:42]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
        df_result.columns = df_result.columns.str.rstrip(".1")

        for idx, row in track(
            df_result.iterrows(),
            total=len(df_result.index),
            description=f"[green]{file} ",
        ):
            for catalog in ["甲", "乙", "丙", "丁", "其他"]:
                for i in ["", "2", "3", "4"]:
                    data = row[f"{catalog}{i}"]
                    if data != "" and "?" not in data and '"' not in data:
                        if not result_trie.has_key(data):
                            result_list.append(data)
                            result_trie[data] = True
                            if not icd_trie.has_key(data):
                                non_icd_list.append(data)

    # Add self-defined icd to final result
    self_icd_df = pd.read_csv(os.path.join(data_path, "self-defined-icd.csv"))
    for data in self_icd_df["diagnosis"]:
        if not result_trie.has_key(data):
            result_list.append(data)
            result_trie[data] = True
        else:
            console.print(f"'{data}' exists in the list.")
    self_icd_df = self_icd_df.sort_values(["diagnosis"])
    self_icd_df.to_csv(os.path.join(data_path, "self-defined-icd.csv"), index=False)

    # Remove certain icd from final result
    exclude_icd_df = pd.read_csv(os.path.join(data_path, "exclude-icd.csv"))
    for data in exclude_icd_df["diagnosis"]:
        if data in result_list:
            result_list.remove(data)
        else:
            console.print(f"'{data}' doesn't exist in the list.")
    exclude_icd_df = exclude_icd_df.sort_values(["diagnosis"])
    exclude_icd_df.to_csv(os.path.join(data_path, "exclude-icd.csv"), index=False)

    # Dump existed diagnosis results which are not in the icd dictionary
    df_non_icd = pd.DataFrame(non_icd_list, columns=["diagnosis"])
    df_non_icd["diagnosis"] = df_non_icd["diagnosis"].str.normalize("NFKC")
    df_non_icd = df_non_icd.sort_values(["diagnosis"])
    df_non_icd.to_csv(os.path.join(data_path, "non-verified-icd.csv"), index=False)

    # Dump final result
    df_result = pd.DataFrame(result_list, columns=["diagnosis"])
    df_result["diagnosis"] = df_result["diagnosis"].str.normalize("NFKC")
    df_result = df_result.sort_values(["diagnosis"])
    df_result.to_csv(os.path.join(data_path, "icd.csv"), index=False)

    # Stop process timing
    end_time = time.time()

    # Print process information
    console.print(
        f'Write into file:\t [cyan bold]{os.path.join(data_path, "icd.csv")}[/]'
    )
    console.print(f"There are {len(non_icd_list)} words not in the icd dictionary.")
    console.print(
        f"Elapsed time:\t [green bold]{round((end_time - start_time), 3)}s[/]"
    )
