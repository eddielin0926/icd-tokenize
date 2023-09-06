import pandas as pd
import pygtrie
import re

from icd_tokenize import ICD


class ICDTokenizer:
    def __init__(self, icd: ICD = None) -> None:
        if icd is None:
            icd = ICD()
        self.trie = pygtrie.CharTrie()
        for element in icd.diagnosis:
            self.trie[element] = True

        self.synonyms = icd.synonyms

    def _pre_process(self, data: str) -> str:
        data = re.sub(r"(?<!合)併(?!發)", "", data)
        data = re.sub(r"合併(?!症)", "", data)
        data = re.sub(r"併發(?!症)", "", data)
        data = re.sub(r"及", "", data)
        data = re.sub(r"並", "", data)
        data = re.sub(r"_", "", data)
        data = re.sub(r"\s", "", data)
        data = data.replace("COVID19", "COVID-19")
        return data

    def _post_process(self, data: list) -> list:
        data = list(dict.fromkeys(data))

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
                result.append(prefix)

        result = self._post_process(result)

        return result
