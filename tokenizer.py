import pandas as pd
import pygtrie
import re


class ICDTokenizer:
    def __init__(self, data) -> None:
        self.trie = pygtrie.CharTrie()
        for element in data:
            self.trie[element] = True

    def _pre_process(self, data: str) -> str:
        data = re.sub(r'(?<!合)併(?!發)', '', data)
        data = re.sub(r'合併(?!症)', '', data)
        data = re.sub(r'併發(?!症)', '', data)
        data = re.sub(r'及', '', data)
        data = re.sub(r'\s', '', data)
        data = data.replace('COVID19', 'COVID-19')
        if __name__ == '__main__':
            print(data)
        return data
    
    def _post_process(self, data: str) -> str:
        if data.upper() == 'COVID-19':
            return 'COVID 19'
        # if '癌術後' in data:
        #     return data.replace('癌術後', '癌')
        return data
        

    def extract_icd(self, input: str):
        input = self._pre_process(input)

        result = []
        while input != "":
            prefix = self.trie.longest_prefix(input).key
            if prefix is None:
                input = input[1:]
            else:
                input = input.removeprefix(prefix)
                prefix = self._post_process(prefix)
                result.append(prefix)
        result = list(dict.fromkeys(result))
        return result


if __name__ == '__main__':
    icd_df = pd.read_csv('./icd/icd.csv')
    icd_series = icd_df['diagnosis']

    tokenizer = ICDTokenizer(icd_series)

    text = 'COVID-19(Covid-19)'

    print(tokenizer.extract_icd(text))
