import os
import time

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import track

# Create rich console
console = Console()

# Start process timing
start_time = time.time()
console.print(":rocket: start processing")

data_dir = "data"
files = os.listdir(data_dir)
files = filter(lambda f: f[:2] != "~$", files)  # Prevent processing temporary excel files

catalogs = []
text = []

type1 = 0  # same
type2 = 1  # transform
type3 = 1  # remove

for file in files:
    # Load Dataset
    df = pd.read_excel(os.path.join(data_dir, file), header=1)
    df = df.drop("NO", axis=1)
    df = df.replace(np.nan, "", regex=True)  # replace nan with empty string

    # Preprocess
    df_input = df.iloc[:, :20]  # 甲, 甲2, ..., 其他3, 其他4
    for col in df_input.columns:
        df_input[col] = df_input[col].str.normalize("NFKC")
    df_target = df.iloc[:, 22:42]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
    df_target.columns = df_target.columns.str.rstrip(".1")  # remove ".1" in column name
    for col in df_target.columns:
        df_target[col] = df_target[col].str.normalize("NFKC")

    for idx, row in track(
        df_input.iterrows(),
        total=len(df_input.index),
        description=f":page_facing_up: [green]{file} ",
        console=console,
    ):
        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            catalog_input = []
            catalog_target = []

            for i in ["", "2", "3", "4"]:
                data = row[f"{catalog}{i}"]
                catalog_input.append(data)
                catalog_target.append(df_target[f"{catalog}{i}"][idx])

            catalog_input = list(filter(lambda x: x != "" and "?" not in x, catalog_input))
            catalog_target = list(filter(lambda x: x != "" and "?" not in x, catalog_target))

            if len(catalog_input) == 0 or len(catalog_target) == 0:
                continue

            if "惡性腫瘤" in str(catalog_input):
                if "惡性腫瘤" in str(catalog_target):
                    type1 += 1
                elif "癌" in str(catalog_target):
                    type2 += 1
                else:
                    type3 += 1
                catalogs.append(catalog_target)
                text.append("。".join(catalog_input))

df = pd.DataFrame({"catalogs": catalogs, "text": text})
df.to_csv("data-惡性腫瘤.csv", index_label="id")

# Finish process timing
end_time = time.time()
elapsed_time = end_time - start_time

# Print final result
total = type1 + type2 + type3
console.print(f'包含有"惡性腫瘤"的輸入共有{total}個')
console.print(f'結果含有"惡性腫瘤"的輸出共有{type1}個，佔{round(type1/total*100, 2)}%')
console.print(f'結果含有"癌"的輸出共有{type2}個，佔{round(type2/total*100, 2)}%')
console.print(f"結果不含兩者的輸出共有{type3}個，佔{round(type3/total*100, 2)}%")
console.print(f":hourglass: elapsed time:\t[green bold]{round(elapsed_time, 3)}s[/]")
