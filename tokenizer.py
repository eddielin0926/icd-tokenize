import pandas as pd
import pygtrie


class ICDTokenizer:
    def __init__(self, data) -> None:
        self.trie = pygtrie.CharTrie()
        for element in data:
            self.trie[element] = True

    def _preprocess(self, input: str) -> str:
        input = input.replace('併', '')
        input =input.replace(' ', '')
        input =input.replace('COVID19', 'COVID 19')
        return input

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
    
    text = '消化道出血併休克'

    print(tokenizer.extract_icd(text))
    
