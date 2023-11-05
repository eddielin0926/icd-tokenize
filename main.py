import argparse
import itertools
import json
import os
import time
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime
from multiprocessing import Manager

import numpy as np
import pandas as pd
from pandas.io.formats import excel
from rich.console import Console
from rich.progress import BarColumn, Progress, TimeRemainingColumn
from rich.table import Table

from icd_tokenize import ICD, ICDTokenizer, ICDValidator, Record

# Disable header style in excel
excel.ExcelFormatter.header_style = None


def processing_file(
    progress,
    task_id,
    tokenizer: ICDTokenizer,
    validator: ICDValidator,
    data_dir: str,
    tmp_record_dir: str,
    file: str,
    output_json: bool = False,
    output_excel: bool = False,
):
    # Extract year and month from file name
    year_month = file[file.find("(") + 1 : file.find(")")]
    year = int(year_month[:3])
    month = int(year_month[3:])

    # Load Dataset
    df = pd.read_excel(os.path.join(data_dir, file), header=1)
    df = df.replace(np.nan, "", regex=True)  # replace nan with empty string

    # Split input and target and normalize data
    df_input = df.iloc[:, 1:21]  # 甲, 甲2, ..., 其他3, 其他4
    for col in df_input.columns:
        df_input[col] = df_input[col].str.normalize("NFKC")
    df_target = df.iloc[:, 23:43]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
    df_target.columns = df_target.columns.str.rstrip(".1")  # remove ".1" in column name
    for col in df_target.columns:
        df_target[col] = df_target[col].str.normalize("NFKC")

    # Tokenize input
    records: list[Record] = []  # store result of each row
    len_of_task = len(df_input.index)
    for idx, row in df_input.iterrows():
        progress[task_id] = {"completed": idx + 1, "total": len_of_task}
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

    # Dump error result
    tmpdir = f"{tmp_record_dir}/{year_month}"
    os.makedirs(f"{tmpdir}")
    errors = itertools.chain.from_iterable([r.get_errors() for r in records if not r.is_correct])
    pd.DataFrame(errors).to_csv(f"{tmpdir}/{year_month}.csv", index=False)

    # Dump json result
    if output_json:
        with open(f"{tmpdir}/{year_month}.json", "w", encoding="utf-8") as f:
            json_records = [e.for_json() for e in records]
            json.dump(json_records, f, ensure_ascii=False)

    # Dump excel result
    if output_excel:
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

    # Collect accuracy
    counts = len(records)
    corrects = [r.is_correct for r in records].count(True)  # count correct records
    dirties = sum([r.dirty for r in records])  # count dirty records

    return {
        "name": year_month,
        "correct": corrects,
        "total": counts,
        "accuracy": corrects * 100 / counts,
        "dirty": dirties,
    }


if __name__ == "__main__":
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
    tokenizer = ICDTokenizer(icd, experimental=True)

    # Load ICD validator
    validator = ICDValidator(icd)

    # List all files in data directory
    data_dir = "data"
    files = os.listdir(data_dir)
    files = list(filter(lambda f: f[:2] != "~$", files))  # Prevent processing temporary excel files
    # files = list(filter(lambda f: "(11104)" in f, files))  # Delete this line to process all files

    stats = []  # statistical data of processing results from each files
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    ) as progress:
        futures: list[Future] = []  # keep track of the jobs
        with Manager() as manager:
            # this is the key - we share some state between our
            # main process and our worker functions
            _progress = manager.dict()
            with ProcessPoolExecutor() as executor:
                for file in files:
                    task_id = progress.add_task(f":page_facing_up: [green]{file}", visible=False)
                    futures.append(
                        executor.submit(
                            processing_file,
                            _progress,
                            task_id,
                            tokenizer,
                            validator,
                            data_dir,
                            tmp_record_dir,
                            file,
                            args.json,
                            args.excel,
                        )
                    )

                # monitor the progress:
                while (n_finished := sum([future.done() for future in futures])) < len(futures):
                    for task_id, update_data in _progress.items():
                        completed = update_data["completed"]
                        total = update_data["total"]
                        # update the progress bar for this task:
                        progress.update(
                            task_id,
                            total=total,
                            completed=completed,
                            visible=(completed > 0),
                        )

                # raise any errors:
                for future in futures:
                    stats.append(future.result())

    # Dump process information
    total_correct = sum([s["correct"] for s in stats])  # count correct records
    total_count = sum([s["total"] for s in stats])  # count total records
    total_accuracy = total_correct * 100 / total_count  # calculate total accuracy
    total_dirty = sum([s["dirty"] for s in stats])  # count dirty records
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
