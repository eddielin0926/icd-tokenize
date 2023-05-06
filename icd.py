import os
import time
import pygtrie
import numpy as np
import pandas as pd
from rich.progress import track
from rich.console import Console


# Create rich console
console = Console()

# Start process timing
start_time = time.time()

icd_df = pd.read_excel('./icd/中文字典_1100712_提供張老師_自定義字典.xlsx')
icd_list = icd_df['中文診斷'].str.normalize('NFKC').to_list()

icd_trie = pygtrie.CharTrie()
for element in icd_list:
    icd_trie[element] = True

not_icd_count = 0
result_list = []
result_trie = pygtrie.CharTrie()

for file in os.listdir('./data'):
    df = pd.read_excel(f'./data/{file}', header=1)
    df = df.drop('NO', axis=1)
    df = df.replace(np.nan, '', regex=True)  # replace nan with empty string

    df_result = df.iloc[:, 22:42]  # 甲.1, 甲2.1, ..., 其他3.1, 其他4.1
    df_result.columns = df_result.columns.str.rstrip('.1')

    for idx, row in track(df_result.iterrows(), total=len(df_result.index), description=f'[green]{file} '):
        for catalog in ['甲', '乙', '丙', '丁', '其他']:
            for i in ['', '2', '3', '4']:
                data = row[f'{catalog}{i}']
                if icd_trie.has_key(data) and not result_trie.has_key(data):
                    not_icd_count += 1
                if not result_trie.has_key(data):
                    if '?' not in data and '"' not in data and data != "":
                        result_list.append(data)
                        result_trie[data] = True


df_result = pd.DataFrame(result_list, columns=['diagnosis'])
df_result['diagnosis'] = df_result['diagnosis'].str.normalize('NFKC')
df_result = df_result.sort_values(['diagnosis'])
df_result.to_csv(f'./icd/icd.csv', index=False)

end_time = time.time()

console.print('Write into file: [cyan bold]icd.csv[/]')
console.print(f'There are {not_icd_count} words not in the icd dictionary.')
console.print(f'Elapsed time:\t [green bold]{round((end_time - start_time), 3)}s[/]')