import pandas as pd
import pygtrie
import re


class ICDTokenizer:
    def __init__(self, data) -> None:
        self.trie = pygtrie.CharTrie()
        for element in data:
            self.trie[element] = True

    def _preprocess(self, data: str) -> str:
        data = re.sub(r'(?<!合)併(?!發)', '', data)
        data = re.sub(r'合併(?!症)', '', data)
        data = re.sub(r'及', '', data)
        data = re.sub(r'\s', '', data)
        data = data.replace('COVID19', 'COVID-19')
        if __name__ == '__main__':
            print(data)
        return data

    def extract_icd(self, input: str):
        input = self._preprocess(input)

        result = []
        while input != "":
            prefix = self.trie.longest_prefix(input).key
            if prefix is None:
                input = input[1:]
            else:
                input = input.removeprefix(prefix)
                if input == 'COVID-19':
                    prefix = 'COVID 19'
                result.append(prefix)
        return result


if __name__ == '__main__':
    icd_df = pd.read_csv('./icd/icd.csv')
    icd_series = icd_df['diagnosis']

    tokenizer = ICDTokenizer(icd_series)

    # text = '慢性疾病及合併症急性發作'
    text = '糖尿病 合併 多重器官 併發症'
    # text = '慢性阻塞性肺病併感染'
    text = '糖尿病及併發症'

    print(tokenizer.extract_icd(text))
