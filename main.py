import argparse
import itertools
import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
from pandas.io.formats import excel
from rich.console import Console
from rich.progress import track
from rich.table import Table

from icd_tokenize import ICD, ICDTokenizer, ICDValidator, Record

# Disable header style in excel
excel.ExcelFormatter.header_style = None

# Parse arguments
parser = argparse.ArgumentParser(prog="icd-tokenize", description="ICD Tokenizer")
parser.add_argument(
    "-j", "--json", help="output result collection in format of json", action="store_true"
)
parser.add_argument(
    "-e", "--excel", help="output result collection in format of excel", action="store_true"
)
args = parser.parse_args()

# Create rich console
console = Console()

# Start process timing
start_time = time.time()
console.print(":rocket: start processing")

# Create temporary directory for storing result
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

# List all files in data directory
data_dir = "data"
files = os.listdir(data_dir)
files = filter(lambda f: f[:2] != "~$", files)  # Prevent processing temporary excel files
files = filter(lambda f: "(11104)" in f, files)  # Delete this line to process all files

stats = []  # statistical data of processing results from each files
total_correct = 0  # number of correct result
total_count = 0  # number of data been processed
total_dirty = 0  # number of dirty data

for file in files:
    # Extract year and month from file name
    year_month = file[file.find("(") + 1 : file.find(")")]
    year = int(year_month[:3])
    month = int(year_month[3:])

    # Load Dataset
    df = pd.read_excel(os.path.join(data_dir, file), header=1)
    df = df.replace(np.nan, "", regex=True)  # replace nan with empty string

    # Preprocess
    df_input = df.iloc[:, 1:21]  # 甲, 甲2, ..., 其他3, 其他4
    for col in df_input.columns:
        df_input[col] = df_input[col].str.normalize("NFKC")
    df_target = df.iloc[:, 23:43]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
    df_target.columns = df_target.columns.str.rstrip(".1")  # remove ".1" in column name
    for col in df_target.columns:
        df_target[col] = df_target[col].str.normalize("NFKC")

    # Prediction
    records: list[Record] = []  # store result of each row
    for idx, row in track(
        df_input.iterrows(),
        total=len(df_input.index),
        description=f":page_facing_up: [green]{file} ",
        console=console,
    ):
        record = Record(
            year=year, month=month, serial=int(df["流水號"][idx]), number=int(df["NO"][idx])
        )
        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            inputs = []
            targets = []
            results = []

            for i in ["", "2", "3", "4"]:
                data = row[f"{catalog}{i}"]
                inputs.append(data)
                targets.append(df_target[f"{catalog}{i}"][idx])
                results.extend(tokenizer.extract_icd(data))

            results = list(dict.fromkeys(results))

            # Extend array length to 4
            while len(results) < 4:
                results.append("")

            # Truncate exceed result
            results = results[:4]

            # Verify result
            record.corrects[catalog] = validator.icd_validate(results, targets)

            # Assign input and result to record
            record.inputs[catalog] = inputs
            record.results[catalog] = results
            record.targets[catalog] = targets

        # Collect result
        records.append(record)

    # Collect accuracy
    counts = len(records)
    corrects = [r.is_correct for r in records].count(True)  # count correct records
    dirties = sum([r.dirty for r in records])  # count dirty records
    stats.append(
        {
            "name": year_month,
            "correct": corrects,
            "total": counts,
            "accuracy": corrects * 100 / counts,
            "dirty": dirties,
        }
    )

    # Add data count
    total_correct += corrects
    total_count += counts
    total_dirty += dirties

    # Dump error result
    tmpdir = f"{tmp_record_dir}/{year_month}"
    os.makedirs(f"{tmpdir}")
    errors = itertools.chain.from_iterable([r.get_errors() for r in records if not r.is_correct])
    pd.DataFrame(errors).to_csv(f"{tmpdir}/{year_month}.csv")

    # Dump json result
    if args.json:
        with open(f"{tmpdir}/{year_month}.json", "w", encoding="utf-8") as f:
            json_records = [e.for_json() for e in records]
            json.dump(json_records, f, ensure_ascii=False)

    # Dump excel result
    if args.excel:
        with pd.ExcelWriter(f"{tmpdir}/{year_month}.xlsx", engine="xlsxwriter") as writer:

            def dump_excel(excels: list[tuple[str, str, str]], sheet_name: str):
                index, before, after = zip(*excels)
                pd.DataFrame(index).to_excel(writer, sheet_name, index=False)
                pd.DataFrame(before).to_excel(writer, sheet_name, index=False, startcol=3)
                pd.DataFrame(after).to_excel(writer, sheet_name, index=False, startcol=24)
                worksheet = writer.sheets[sheet_name]
                worksheet.write_string(0, 2, "斷詞前")
                worksheet.write_string(0, 23, "斷詞後")

            dump_excel([e.for_excel() for e in records if e.is_correct], f"{year_month}_斷詞正確")
            dump_excel(
                [e.for_excel() for e in records if not e.is_correct], f"{year_month}_斷詞錯誤"
            )


# Dump process information
total_accuracy = total_correct * 100 / total_count
total_stats = stats + [
    {
        "name": "total",
        "correct": total_correct,
        "total": total_count,
        "accuracy": total_accuracy,
        "dirty": total_dirty,
    }
]
df_stats = pd.DataFrame(total_stats, index=None)
df_stats.to_csv(f"{tmp_record_dir}/result.csv", index=False)

# Display result Table of each file
table = Table(title="Result", show_footer=True)
table.add_column("File", footer="Total")
table.add_column("Correct", footer=str(total_correct))
table.add_column("Total", footer=str(total_count))
table.add_column("Accuracy", footer=f"{total_accuracy:.2f}%")
table.add_column("Dirty", footer=str(total_dirty))
for s in stats:
    table.add_row(
        s["name"],
        str(s["correct"]),
        str(s["total"]),
        f"{s['accuracy']:.2f}%",
        str(s["dirty"]),
    )
console.print(table)

# Finish process timing
end_time = time.time()
elapsed_time = end_time - start_time

# Print final result
console.print(f":white_check_mark: total accuracy:\t[green bold]{round(total_accuracy, 2)}%[/]")
console.print(f":floppy_disk: total data:\t\t[green bold]{total_count}[/]")
console.print(f":hourglass: elapsed time:\t[green bold]{round(elapsed_time, 3)}s[/]")
