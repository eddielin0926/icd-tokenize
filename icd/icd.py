import os
import numpy as np
import pandas as pd
from tqdm import tqdm


icd_df = pd.read_excel('./中文字典_1100712_提供張老師_自定義字典.xlsx')
icd_list = icd_df['中文診斷'].str.normalize('NFKC').to_list()

result_list = []

for file in os.listdir('../data'):
    print(f'{file}')

    df = pd.read_excel(f'../data/{file}', header=1)
    df = df.drop('NO', axis=1)
    df = df.replace(np.nan, '', regex=True)  # replace nan with empty string

    df_result = df.iloc[:, 22:42]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
    df_result.columns = df_result.columns.str.rstrip('.1')

    for idx, row in tqdm(df_result.iterrows(), total=len(df_result.index)):
        for catalog in ['甲', '乙', '丙', '丁', '其他']:
            for i in ['', '2', '3', '4']:
                data = row[f'{catalog}{i}']
                if data in icd_list and data not in result_list:
                    result_list.append(data)

df_result = pd.DataFrame(result_list, columns=['diagnosis'])
df_result.to_csv(f'icd.csv', index=False)
