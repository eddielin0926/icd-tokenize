import os
import time
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from datetime import datetime
from tokenizer import ICDTokenizer
from rich.progress import track


# Start process timing
start_time = time.time()

# Create rich console
console = Console()

# Create tmp directory
if not os.path.exists('tmp'):
    os.makedirs('tmp')
timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
tmp_record_dir = f'tmp/{timestamp}'
os.makedirs(tmp_record_dir)

# Load ICD Dictionary
icd_df = pd.read_csv('./icd/icd.csv')
icd_series = icd_df['diagnosis']

# Load ICD tokenizer
tokenizer = ICDTokenizer(icd_series)

records = []
total_correct = 0
total_count = 0
for file in os.listdir('./data'):
    if file[:2] == '~$':  # Prevent processing temporary excel files
        continue

    # Load Dataset
    df = pd.read_excel(f'./data/{file}', header=1)
    df = df.drop('NO', axis=1)
    df = df.replace(np.nan, '', regex=True)  # replace nan with empty string

    # Preprocess
    df_input = df.iloc[:, :20]  # 甲, 甲2, ..., 其他3, 其他4
    for col in df_input.columns:
        df_input[col] = df_input[col].str.normalize('NFKC')
    df_target = df.iloc[:, 22:42]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
    df_target.columns = df_target.columns.str.rstrip('.1')
    for col in df_target.columns:
        df_target[col] = df_target[col].str.normalize('NFKC')

    # Prediction
    input_list = []
    error_list = []
    answer_list = []
    correct_count = 0
    current_count = 0
    is_dirty_data = False
    for idx, row in track(df_input.iterrows(), total=len(df_input.index), description=f'[green]{file} '):
        row_result = []
        for catalog in ['甲', '乙', '丙', '丁', '其他']:
            catalog_result = []
            for i in ['', '2', '3', '4']:
                data = row[f'{catalog}{i}']

                if '?' in data:  # Unreadable character in string
                    is_dirty_data = True

                col_result = tokenizer.extract_icd(data)
                catalog_result.extend(col_result)

            # Extend array length to 4
            while len(catalog_result) < 4:
                catalog_result.append('')

            # Truncate exceed result
            row_result.extend(catalog_result[:4])

        if is_dirty_data:
            is_dirty_data = False
            continue  # skip dirty data

        row_target = df_target.iloc[idx].to_list()
        current_count += 1

        if row_result == row_target:  # result is correct
            correct_count += 1
        else:
            # From 1x20 reshape to 5x4
            row_input = [row.to_list()[4*i:4*(i+1)] for i in range(5)]
            row_result = [row_result[4*i:4*(i+1)] for i in range(5)]
            row_target = [row_target[4*i:4*(i+1)] for i in range(5)]

            # Collect error records
            for inp, res, tar in zip(row_input, row_result, row_target):
                if res != tar:
                    input_list.append(inp)
                    error_list.append(res)
                    answer_list.append(tar)

    # Collect accuracy
    accuracy = (correct_count * 100 / current_count)
    records.append({
        "name": file,
        "correct": correct_count,
        "total": current_count,
        "accuracy": accuracy
    })

    # Add data count
    total_correct += correct_count
    total_count += current_count

    # Dump error records
    tmpdir = f'{tmp_record_dir}/{file[:7]}'
    os.makedirs(f'{tmpdir}')
    pd.DataFrame(input_list).to_csv(f'{tmpdir}/input.csv')
    pd.DataFrame(error_list).to_csv(f'{tmpdir}/error.csv')
    pd.DataFrame(answer_list).to_csv(f'{tmpdir}/answer.csv')

# Dump process information
total_accuracy = (total_correct * 100 / total_count)
df_record = pd.DataFrame(records, index=None)
df_total = pd.DataFrame([{
    "name": 'total',
    "correct": total_correct,
    "total": total_count,
    "accuracy": total_accuracy
}])
df_record = pd.concat([df_record, df_total], ignore_index=True)
df_record.to_csv(f'{tmp_record_dir}/result.csv', index=False)

# Print accuracy table
table = Table(title='Result')
table.add_column('Name')
table.add_column('Correct / Total')
table.add_column('Accuracy')
for record in records:
    table.add_row(
        record['name'], f"{record['correct']} / {record['total']}", f"{round(record['accuracy'], 1)}%")
console.print(table)

# Finish process timing
end_time = time.time()

# Print result
console.print(f'total accuracy:\t [green bold]{round(total_accuracy, 2)}%[/]')
console.print(f'total data:\t [green bold]{total_count}[/]')
console.print(
    f'elapsed time:\t [green bold]{round((end_time - start_time), 3)}s[/]')
