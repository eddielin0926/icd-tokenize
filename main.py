import os
import fnmatch
import pandas as pd
import pygtrie
import numpy as np

# Load ICD Dictionary
icd_df = pd.read_excel('./中文字典_1100712_提供張老師_自定義字典.xlsx')
icd_series = icd_df['中文診斷'].str.normalize('NFKC')


# Create ICD Trie
icd_trie = pygtrie.CharTrie()
for entry in icd_series:
    icd_trie[entry] = True


for file in os.listdir('./data'):
    print(file)

    # Load Dataset
    df = pd.read_excel(f'./data/{file}', header=1)
    df = df.drop('NO', axis=1)
    df = df.replace(np.nan, '', regex=True)  # replace nan with empty string


    # Preprocess
    df_input = df.iloc[:, :20]  # 甲, 甲2, ..., 其他3, 其他4
    df_target = df.iloc[:, 22:42]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
    df_target.columns = df_target.columns.str.rstrip('.1')


    # Extract ICD from input string
    def extract_icd(data):
        result = []
        while data != "":
            prefix = icd_trie.longest_prefix(data).key
            if prefix is None:
                data = data.removeprefix(data[0])
            else:
                data = data.removeprefix(prefix)
                result.append(prefix)
        return result


    # Prediction
    correct_count = 0
    for idx, row in df_input.iterrows():
        row_result = []
        for catalog in ['甲', '乙', '丙', '丁', '其他']:
            catalog_result = []
            for i in ['', '2', '3', '4']:
                data = row[f'{catalog}{i}']
                col_result = extract_icd(data)
                catalog_result.extend(col_result)
            while len(catalog_result) < 4:
                catalog_result.append('')
            row_result.extend(catalog_result)
        row_target = df_target.iloc[idx].to_list()
        if row_result == row_target:
            correct_count += 1
        
    rate = (correct_count * 100 / len(df_target.index))
    print(f'accuracy: {round(rate, 2)}%')
