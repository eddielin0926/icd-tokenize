import pandas as pd
import pygtrie


class ICDTokenizer:
    def __init__(self, data) -> None:
        self.trie = pygtrie.CharTrie()
        for element in data:
            self.trie[element] = True

    def extract_icd(self, input):
        result = []
        can_skip = False
        while input != "":
            prefix = self.trie.longest_prefix(input).key
            if prefix is None:
                input = input[1:]
                if can_skip:
                    if self.trie.has_subtrie(result[-1]):
                        prefix = self.trie.longest_prefix(result[-1]+input).key
                        result[-1] = prefix
                        input = (result[-1]+input).removeprefix(prefix)
                can_skip = False
            else:
                input = input.removeprefix(prefix)
                result.append(prefix)
                can_skip = True
        return result


if __name__ == '__main__':
    icd_df = pd.read_csv('./icd/icd.csv')
    icd_series = icd_df['diagnosis']
    
    tokenizer = ICDTokenizer(icd_series)
    
    text = '十二指腸潰瘍併穿孔'

    print(tokenizer.extract_icd(text))
    
