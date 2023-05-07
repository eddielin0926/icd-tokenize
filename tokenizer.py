import pandas as pd
import pygtrie
import re


class ICDTokenizer:
    def __init__(self, data, path='icd/synonyms.txt') -> None:
        self.trie = pygtrie.CharTrie()
        for element in data:
            self.trie[element] = True
        
        with open(path, 'r', encoding="utf-8") as f:
            self.synonyms_list = []
            for line in f.readlines():
                line = line.replace('\n', '')
                self.synonyms_list.append(line.split(','))


    def _pre_process(self, data: str) -> str:
        data = re.sub(r'(?<!合)併(?!發)', '', data)
        data = re.sub(r'合併(?!症)', '', data)
        data = re.sub(r'併發(?!症)', '', data)
        data = re.sub(r'及', '', data)
        data = re.sub(r'並', '', data)
        data = re.sub(r'_', '', data)
        data = re.sub(r'\s', '', data)
        data = data.replace('COVID19', 'COVID-19')
        if __name__ == '__main__':
            print(f'pre-process: {data}')
        return data   

    def _post_process(self, data: list) -> list:
        # switch to synonym
        for i in range(len(data)):
            for synonym in self.synonyms_list:
                if data[i] in synonym:
                    data[i] = synonym[0]

        # # remove subset words
        # result = []
        # for i in range(len(data)):
        #     is_subset = False
        #     for j in range(len(data)):
        #         if i != j:
        #             if data[i] in data[j]:
        #                 is_subset = True
        #                 break
        #     if not is_subset:
        #         result.append(data[i])

        data = list(dict.fromkeys(data))

        return data

    def extract_icd(self, input: str):
        input = self._pre_process(input)

        result = []
        while input != "":
            prefix = self.trie.longest_prefix(input).key
            if prefix is None:
                # if self.trie.has_subtrie(input[0]):
                #     count = 0
                #     while count < (len(input) - 1):
                #         if self.trie.has_key(input[0] + input[count:]):
                #             prefix = input[0] + input[count:]
                #             result.append(prefix)
                #             break
                #         count += 1
                input = input[1:]
            else:
                input = input.removeprefix(prefix)
                result.append(prefix)

        result = self._post_process(result)

        return result


if __name__ == '__main__':
    icd_df = pd.read_csv('./icd/icd.csv')
    icd_series = icd_df['diagnosis']

    tokenizer = ICDTokenizer(icd_series)

    text = '肺左上葉及右中葉鱗狀細胞癌'

    print(f'input text: {text}')

    result = tokenizer.extract_icd(text)

    print(f'result list: {result}')
