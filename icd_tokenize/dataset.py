"""
This script is used to generate dataset from excel files.
"""
import os

import numpy as np
import pandas as pd
import pyarrow
from datasets import ClassLabel, Dataset, Features, Sequence, Value

pyarrow.PyExtensionType.set_auto_load(True)


icd_df = pd.read_csv("icd_tokenize/data/original-icd.csv")
icd_dict = dict(zip(icd_df["diagnosis"], icd_df["ICD1"]))
icd_set = set(icd_dict.values())
class_labels = ClassLabel(num_classes=len(icd_set), names=list(icd_set))


def generate_data():
    data_dir = "data"
    files = os.listdir(data_dir)
    files = filter(lambda f: f[:2] != "~$", files)  # Prevent processing temporary excel files
    files = list(filter(lambda f: "(00000)" not in f, files))

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

        for _, row in df.iterrows():
            for i, catalog in enumerate(["甲", "乙", "丙", "丁", "其他"]):
                input_data = []
                target_data = []

                for tag in ["", "2", "3", "4"]:
                    input_data.append(row[f"{catalog}{tag}"])
                    target_data.append(row[f"{catalog}{tag}.1"])

                input_data = list(filter(lambda x: x != "", input_data))
                target_data = list(filter(lambda x: x != "", target_data))
                icd_data = [icd_dict.get(icd, "R97") for icd in target_data]
                class_data = [class_labels.str2int(icd) for icd in icd_data]

                yield {
                    "year": year + 1911,
                    "month": month,
                    "no": row["NO"],
                    "death": row["死亡方式"],
                    "input_code": row["創傷代號"],
                    "result_code": row["創傷代號.1"],
                    "check": row["創傷代號\n檢查"],
                    "serial_no": row["流水號"],
                    "catalog": i,
                    "inputs": input_data,
                    "results": target_data,
                    "icds": icd_data,
                    "encodes": class_data,
                }


features = Features(
    {
        "year": Value("int32"),
        "month": Value("int32"),
        "no": Value("int32"),
        "death": Value("int32"),
        "input_code": Value("int32"),
        "result_code": Value("int32"),
        "check": Value("bool"),
        "serial_no": Value("int32"),
        "catalog": Value("int32"),
        "inputs": Sequence(Value("string")),
        "results": Sequence(Value("string")),
        "icds": Sequence(Value("string")),
        "encodes": Sequence(class_labels),
    }
)

dataset = Dataset.from_generator(generate_data, features=features)
dataset.push_to_hub("eddielin0926/chinese-icd")
