import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import track
from rich.table import Table

from icd_tokenize import ICD, ICDTokenizer, ICDValidator


def percent(a, b, digit=2):
    return str(round((a / b) * 100, digit)) + "%"


# Create rich console
console = Console()

# Start process timing
start_time = time.time()
console.print(":rocket: start processing")

# Create tmp directory
if not os.path.exists("tmp"):
    os.makedirs("tmp")
timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
tmp_record_dir = f"tmp/{timestamp}"
os.makedirs(tmp_record_dir)
console.print(
    f":open_file_folder: create output directory: [yellow]{os.path.abspath(tmp_record_dir)}[/]"
)

# Load ICD Dictionary
icd = ICD()

# Load ICD tokenizer
tokenizer = ICDTokenizer(icd)

# Load ICD validator
validator = ICDValidator(icd)

records = []  # statistical data of processing results from each files
total_correct = 0  # number of correct result
total_count = 0  # number of data been processed
total_dirty = 0  # number of dirty data

data_dir = "data"
files = os.listdir(data_dir)
files = filter(lambda f: f[:2] != "~$", files)  # Prevent processing temporary excel files
# files = filter(lambda f: "(11102)" in f, files)  # Delete this line to process all files

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

    # Prediction
    inputs = []
    errors = []
    answers = []
    corrects = 0
    dirties = 0
    total = len(df_input.index)
    for idx, row in track(
        df_input.iterrows(),
        total=total,
        description=f":page_facing_up: [green]{file} ",
        console=console,
    ):
        is_row_correct = True
        is_dirty_data = False
        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            catalog_input = []
            catalog_target = []
            catalog_result = []

            for i in ["", "2", "3", "4"]:
                data = row[f"{catalog}{i}"]
                catalog_input.append(data)
                catalog_target.append(df_target[f"{catalog}{i}"][idx])

                if "?" in data:  # Unreadable character in string
                    is_dirty_data = True

                if data != "":
                    col_result = tokenizer.extract_icd(data)
                    catalog_result.extend(col_result)

            catalog_result = list(dict.fromkeys(catalog_result))

            # Extend array length to 4
            while len(catalog_result) < 4:
                catalog_result.append("")

            # Truncate exceed result
            catalog_result = catalog_result[:4]

            if not validator.icd_validate(catalog_result, catalog_target):
                is_row_correct = False

                # Collect error records
                inputs.append(catalog_input)
                errors.append(catalog_result)
                answers.append(catalog_target)

        if is_row_correct:
            corrects += 1
        if is_dirty_data:
            dirties += 1

    # Collect accuracy
    records.append(
        {
            "name": file,
            "correct": corrects,
            "total": total,
            "accuracy": corrects * 100 / total,
            "dirty": dirties,
        }
    )

    # Add data count
    total_correct += corrects
    total_count += total
    total_dirty += dirties

    # Dump error records
    tmpdir = f"{tmp_record_dir}/{file[:7]}"
    os.makedirs(f"{tmpdir}")
    pd.DataFrame(inputs).to_csv(f"{tmpdir}/input.csv")
    pd.DataFrame(errors).to_csv(f"{tmpdir}/error.csv")
    pd.DataFrame(answers).to_csv(f"{tmpdir}/answer.csv")


# Dump process information
total_accuracy = total_correct * 100 / total_count
df_record = pd.DataFrame(records, index=None)
df_total = pd.DataFrame(
    [
        {
            "name": "total",
            "correct": total_correct,
            "total": total_count,
            "accuracy": total_accuracy,
            "dirty": total_dirty,
        }
    ]
)
df_record = pd.concat([df_record, df_total], ignore_index=True)
df_record.to_csv(f"{tmp_record_dir}/result.csv", index=False)

# Display result Table of each file
table = Table(title="Result")
table.add_column("File")
table.add_column("Correct / Total")
table.add_column("Accuracy")
table.add_column("Dirty")
for record in records:
    table.add_row(
        record["name"],
        f"{record['correct']} / {record['total']}",
        percent(record["correct"], record["total"]),
        percent(record["dirty"], record["total"]),
    )
console.print(table)

# Finish process timing
end_time = time.time()
elapsed_time = end_time - start_time

# Print final result
console.print(f":white_check_mark: total accuracy:\t[green bold]{round(total_accuracy, 2)}%[/]")
console.print(f":floppy_disk: total data:\t\t[green bold]{total_count}[/]")
console.print(f":hourglass: elapsed time:\t[green bold]{round(elapsed_time, 3)}s[/]")
