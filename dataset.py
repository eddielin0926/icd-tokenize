"""
This script is used to generate dataset from excel files.
"""
import os

import numpy as np
import pandas as pd
import pyarrow
from datasets import Array2D, Dataset, Features, Value
from rich.progress import track

pyarrow.PyExtensionType.set_auto_load(True)

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
    df[["NO", "死亡方式", "創傷代號", "創傷代號.1", "創傷代號\n檢查", "流水號"]] = df[
        ["NO", "死亡方式", "創傷代號", "創傷代號.1", "創傷代號\n檢查", "流水號"]
    ].fillna(0)
    df = df.replace(np.nan, "", regex=True)  # replace nan with empty string

    input_data = []
    target_data = []
    for idx, row in track(df.iterrows(), total=len(df.index), description=f"{file} "):
        input_data.append([])
        target_data.append([])
        for i, catalog in enumerate(["甲", "乙", "丙", "丁", "其他"]):
            input_data[-1].append([])
            target_data[-1].append([])
            for tag in ["", "2", "3", "4"]:
                input_data[-1][-1].append(row[f"{catalog}{tag}"])
                target_data[-1][-1].append(row[f"{catalog}{tag}.1"])

    df["inputs"] = input_data
    df["labels"] = target_data

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
            "創傷代號.1": "result_code",
            "創傷代號\n檢查": "check",
            "流水號": "serial_no",
        },
        inplace=True,
    )

    # df.to_csv(f"dataset/{year + 1911}-{str(month).zfill(2)}.csv", index=False)
    df_list.append(df)

df = pd.concat(df_list, ignore_index=True)

features = Features(
    {
        "year": Value("int32"),
        "month": Value("int32"),
        "no": Value("int32"),
        "inputs": Array2D(shape=(5, 4), dtype="string"),
        "labels": Array2D(shape=(5, 4), dtype="string"),
        "death": Value("int32"),
        "input_code": Value("int32"),
        "result_code": Value("int32"),
        "check": Value("bool"),
        "serial_no": Value("int32"),
    }
)

dataset = Dataset.from_pandas(df, features=features)
dataset.push_to_hub("eddielin0926/chinese-icd")
