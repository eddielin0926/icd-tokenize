import os
import time
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from tokenizer import ICDTokenizer


start_time = time.time()

# Create tmp directory
if not os.path.exists('tmp'):
    os.makedirs('tmp')
timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
tmp_record_dir = f'tmp/{timestamp}'
os.makedirs(tmp_record_dir)


# Load ICD Dictionary
icd_df = pd.read_csv('./icd/icd.csv')
icd_series = icd_df['diagnosis']


tokenizer = ICDTokenizer(icd_series)


total_correct = 0
total_count = 0
for file in os.listdir('./data'):
    if file[:2] == '~$':
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
    for idx, row in tqdm(df_input.iterrows(), total=len(df_input.index), leave=True):
        row_result = []
        for catalog in ['甲', '乙', '丙', '丁', '其他']:
            catalog_result = []
            for i in ['', '2', '3', '4']:
                data = row[f'{catalog}{i}']
                col_result = tokenizer.extract_icd(data)
                catalog_result.extend(col_result)

            # Extend array length to 4
            while len(catalog_result) < 4:
                catalog_result.append('')
            row_result.extend(catalog_result[:4])  # truncate exceed result

        row_target = df_target.iloc[idx].to_list()
        if row_result == row_target:  # result is correct
            correct_count += 1
        else:
            # From 1x20 reshape to 5x4
            row_input = [row.to_list()[4*i:4*(i+1)] for i in range(5)]
            row_result = [row_result[4*i:4*(i+1)] for i in range(5)]
            row_target = [row_target[4*i:4*(i+1)] for i in range(5)]

            for inp, res, tar in zip(row_input, row_result, row_target):
                if res != tar:
                    input_list.append(inp)
                    error_list.append(res)
                    answer_list.append(tar)

    rate = (correct_count * 100 / len(df_target.index))
    print(f'{file}\t {correct_count} / {len(df_target.index)}\t {round(rate, 1)}%')

    total_correct += correct_count
    total_count += len(df_target.index)

    # Save error records
    df_origin = pd.DataFrame(input_list)
    df_error = pd.DataFrame(error_list)
    df_answer = pd.DataFrame(answer_list)

    tmpdir = f'{tmp_record_dir}/{file[:7]}'
    os.makedirs(f'{tmpdir}')
    df_origin.to_csv(f'{tmpdir}/input.csv')
    df_error.to_csv(f'{tmpdir}/error.csv')
    df_answer.to_csv(f'{tmpdir}/answer.csv')

end_time = time.time()

rate = (total_correct * 100 / total_count)
print(f'total accuracy:\t {round(rate, 2)}%')
print(f'total data:\t {total_count}')
print(f'elapsed time: {end_time - start_time}')