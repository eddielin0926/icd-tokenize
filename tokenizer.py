import pandas as pd
import pygtrie


class ICDTokenizer:
    def __init__(self, data) -> None:
        self.trie = pygtrie.CharTrie()
        for element in data:
            self.trie[element] = True

    def extract_icd(self, input):
        result = []
        while input != "":
            prefix = self.trie.longest_prefix(input).key
            if prefix is None:
                input = input.removeprefix(input[0])
            else:
                input = input.removeprefix(prefix)
                result.append(prefix)
        return result


if __name__ == '__main__':
    icd_df = pd.read_csv('./icd/icd.csv')
    icd_series = icd_df['diagnosis']
    
    tokenizer = ICDTokenizer(icd_series)
    
    text = '十二指腸潰瘍併穿孔'

    print(tokenizer.extract_icd(text))
    
