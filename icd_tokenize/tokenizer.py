import itertools
import re

import pygtrie

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

        if "行人" in data:
            if "機車" in data:
                data = "車禍B1行人*機車"
            elif "摩托車" in data:
                data = "車禍B1行人*機車"
            elif "小客車" in data:
                data = "車禍B2行人*汽車"
            elif "大貨車" in data:
                data = "車禍B4行人*大貨車"
            elif "大客車" in data:
                data = "車禍B4行人*大貨車"
            elif "貨車" in data:
                data = "車禍B3行人*貨車"
            elif "火車" in data:
                data = "車禍B6行人*火車"
        elif "機車騎士" in data:
            if "小客車" in data:
                data = "車禍D1機車騎士*汽車"
            elif "汽車" in data:
                data = "車禍D1機車騎士*汽車"
            elif "大貨車" in data:
                data = "車禍D3機車騎士*大貨車"
            elif "貨車" in data:
                data = "車禍D2機車騎士*貨車"
            elif "腳踏車" in data:
                data = "車禍D0機車騎士*腳踏車"
            elif "曳引車" in data:
                data = "車禍D3機車騎士*曳引車"
            elif "自行車" in data:
                data = "車禍D0機車騎士*腳踏車"
        elif "機車" in data:
            if "小客車" in data or "汽車" in data:
                data = "車禍A21機車*汽車"
            elif "大貨車" in data:
                data = "車禍D3機車騎士*大貨車"
            elif "貨車" in data:
                data = "車禍A22機車*貨車"
            elif data.count("機車") == 2:
                data = "車禍A20機車"
        elif "自行車" in data or "腳踏車" in data:
            if "小客車" in data or "汽車" in data:
                data = "車禍C2腳踏車騎士*汽車"
            elif "機車" in data:
                data = "車禍C1腳踏車騎士*機車"
            elif "摩托車" in data:
                data = "車禍C1腳踏車騎士*機車"
            elif "貨車" in data:
                data = "車禍C3腳踏車騎士*小貨車"

        return data

    def is_subset(self, str1: str, str2: str) -> bool:
        if str1 == str2:
            return False
        if len(str1) > len(str2):
            str1, str2 = str2, str1
        for i in str1:
            if i not in str2:
                return False
        return True

    def _post_process(self, data: list) -> list:
        data = list(dict.fromkeys(data))
        data.sort(key=lambda s: len(s), reverse=True)

        result = []
        for s in data:
            if not any([self.is_subset(s, r) for r in result]):
                result.append(s)

        return result

    def extract_icd(self, input_str: str):
        input_str = self._pre_process(input_str)

        result = []
        while input_str != "":
            prefix = self.trie.longest_prefix(input_str).key
            if prefix is None:
                if self.trie.has_subtrie(input_str[0]):
                    tmp_input = input_str[1:]
                    length = len(tmp_input)
                    for i in range(length, 1, -1):
                        for e in list(itertools.combinations(tmp_input, i)):
                            s = "".join(e)
                            if self.trie.has_key(input_str[0] + s):
                                result.append(input_str[0] + s)
                input_str = input_str[1:]
            else:
                input_str = input_str.removeprefix(prefix)
                result.append(prefix)

        result = self._post_process(result)

        return result


if __name__ == "__main__":
    tokenizer = ICDTokenizer()
    string = "大腸直腸癌伴有肺部、肝臟轉移"
    # string = "女性右側乳房未明示部位惡性腫瘤"
    # string = "上葉之左側支氣管或肺惡性腫瘤"
    # string = "右上肺葉惡性腫瘤"
    # string = "子宮肌層肉瘤末期"
    # string = "乳腺惡性腫瘤"
    # string = "上消化道大出血"
    # string = "心肺腎衰竭"
    # string = "瀰漫大B細胞淋巴瘤"
    print(tokenizer.extract_icd(string))
