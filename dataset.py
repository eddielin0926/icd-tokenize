"""
This script is used to generate dataset from excel files.
"""
import os

import numpy as np
import pandas as pd
from rich.progress import track

data_dir = "data"
files = os.listdir(data_dir)
files = filter(lambda f: f[:2] != "~$", files)  # Prevent processing temporary excel files
files = list(filter(lambda f: "(00000)" not in f, files))

catalogs = []
text = []
df_list = []
for file in files:
    year_month = file[file.find("(") + 1 : file.find(")")]
    year = int(year_month[:3])
    month = int(year_month[3:])

    # Load Dataset
    df = pd.read_excel(os.path.join(data_dir, file), header=1)
    df = df.replace(np.nan, "", regex=True)  # replace nan with empty string

    input_data_list = [[], [], [], [], []]
    target_data_list = [[], [], [], [], []]
    for idx, row in track(df.iterrows(), total=len(df.index), description=f"{file} "):
        data = {}
        for i, catalog in enumerate(["甲", "乙", "丙", "丁", "其他"]):
            input_data = []
            target_data = []

            for tag in ["", "2", "3", "4"]:
                input_data.append(row[f"{catalog}{tag}"])
                target_data.append(row[f"{catalog}{tag}.1"])

            input_data = list(filter(lambda x: x != "", input_data))
            target_data = list(filter(lambda x: x != "", target_data))

            input_data_list[i].append(input_data)
            target_data_list[i].append(target_data)

    for i in range(5):
        df[f"input_{i}"] = input_data_list[i]
    for i in range(5):
        df[f"target_{i}"] = target_data_list[i]

    df = df.drop(
        columns=[f"{c}{i}" for c in ["甲", "乙", "丙", "丁", "其他"] for i in ["", "2", "3", "4"]]
    )
    df = df.drop(
        columns=[f"{c}{i}.1" for c in ["甲", "乙", "丙", "丁", "其他"] for i in ["", "2", "3", "4"]]
    )

    df.insert(0, "year", year + 1911)
    df.insert(1, "month", month)

    df.rename(
        columns={
            "NO": "no",
            "死亡方式": "death",
            "創傷代號": "input_code",
            "創傷代號.1": "target_code",
            "創傷代號\n檢查": "check",
            "流水號": "serial_no",
        },
        inplace=True,
    )

    df.to_csv(f"dataset/{year + 1911}_{str(month).zfill(2)}.csv", index=False)

    df_list.append(df)

df = pd.concat(df_list, ignore_index=True)
df.to_csv("dataset/data.csv", index=False)
