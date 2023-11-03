import argparse
import json
import os
import re
import time
from datetime import datetime

import numpy as np
import pandas as pd
from pandas.io.formats import excel
from rich.console import Console
from rich.progress import track
from rich.table import Table

from icd_tokenize import ICD, ICDTokenizer, ICDValidator, Record

excel.ExcelFormatter.header_style = None

parser = argparse.ArgumentParser(prog="icd-tokenize", description="ICD Tokenizer")
parser.add_argument("-j", "--json", help="output json file", action="store_true")
parser.add_argument("-e", "--excel", help="output excel file", action="store_true")
args = parser.parse_args()


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

stats = []  # statistical data of processing results from each files
total_correct = 0  # number of correct result
total_count = 0  # number of data been processed
total_dirty = 0  # number of dirty data

data_dir = "data"
files = os.listdir(data_dir)
files = filter(lambda f: f[:2] != "~$", files)  # Prevent processing temporary excel files
files = filter(lambda f: "(11104)" in f, files)  # Delete this line to process all files


for file in files:
    # Extract year and month from file name
    year_month = file[file.find("(") + 1 : file.find(")")]
    year = int(year_month[:3])
    month = int(year_month[3:])

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
    records: list[Record] = []  # store result of each row
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
        result = Record(year=year, month=month, serial=int(df["流水號"][idx]), number=idx + 1)

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

            # Assign result to record
            result.inputs[catalog] = catalog_input
            result.tokens[catalog] = catalog_result

            # Verify result
            if not validator.icd_validate(catalog_result, catalog_target):
                is_row_correct = False

                # Collect error result
                inputs.append(catalog_input)
                errors.append(catalog_result)
                answers.append(catalog_target)

        # Collect result
        records.append(result)

        if is_row_correct:
            corrects += 1
            result.is_correct = True
        if is_dirty_data:
            dirties += 1

    # Collect accuracy
    name = re.search(r"\((.*?)\)", file).group(1)
    stats.append(
        {
            "name": name,
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

    # Dump error result
    tmpdir = f"{tmp_record_dir}/{name}"
    os.makedirs(f"{tmpdir}")
    pd.DataFrame(inputs).to_csv(f"{tmpdir}/input.csv")
    pd.DataFrame(errors).to_csv(f"{tmpdir}/error.csv")
    pd.DataFrame(answers).to_csv(f"{tmpdir}/answer.csv")

    # Dump json result
    if args.json:
        with open(f"{tmpdir}/{year_month}.json", "w", encoding="utf-8") as f:
            json_records = [e.for_json() for e in records]
            json.dump(json_records, f, ensure_ascii=False)

    # Dump excel result
    if args.excel:
        with pd.ExcelWriter(f"{tmpdir}/{year_month}.xlsx") as writer:
            excel_correct = [e.for_excel() for e in records if e.is_correct]
            pd.DataFrame(excel_correct).to_excel(
                writer, sheet_name=f"{year_month}_斷詞正確", index=False
            )
            worksheet = writer.sheets[f"{year_month}_斷詞正確"]
            shift = 0
            for catalog in ["甲", "乙", "丙", "丁", "其他"]:
                for i in ["", "2", "3", "4"]:
                    worksheet.write_string(0, 24 + shift, f"{catalog}{i}")
                    shift += 1

            excel_error = [e.for_excel() for e in records if not e.is_correct]
            pd.DataFrame(excel_error).to_excel(
                writer, sheet_name=f"{year_month}_斷詞錯誤", index=False
            )

            worksheet = writer.sheets[f"{year_month}_斷詞錯誤"]
            shift = 0
            for catalog in ["甲", "乙", "丙", "丁", "其他"]:
                for i in ["", "2", "3", "4"]:
                    worksheet.write_string(0, 24 + shift, f"{catalog}{i}")
                    shift += 1


# Dump process information
total_accuracy = total_correct * 100 / total_count
df_record = pd.DataFrame(stats, index=None)
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
table.add_column("Correct")
table.add_column("Total")
table.add_column("Accuracy")
table.add_column("Dirty")
for record in stats:
    table.add_row(
        record["name"],
        str(record["correct"]),
        str(record["total"]),
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
