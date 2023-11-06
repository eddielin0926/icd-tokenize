import re

import pygtrie

from icd_tokenize import ICD


class ICDTokenizer:
    def __init__(self, icd: ICD = None, experimental=False) -> None:
        if icd is None:
            icd = ICD()
        self.trie = pygtrie.CharTrie()
        for element in icd.diagnosis:
            self.trie[element] = True

        self.synonyms = icd.synonyms

        self.experimental = experimental

    def _pre_process(self, data: str) -> str:
        data = re.sub(r"(?<!合)併(?!發)", "", data)
        data = re.sub(r"合併(?!症)", "", data)
        data = re.sub(r"併發(?!症)", "", data)
        data = re.sub(r"無明顯外傷性死因", "", data)
        data = re.sub(r"無外傷性死因", "", data)
        data = re.sub(r"無明顯外傷", "", data)
        data = re.sub(r"非新冠肺炎", "", data)
        data = re.sub(r"未明", "", data)
        data = re.sub(r"及", "", data)
        data = re.sub(r"並", "", data)
        data = re.sub(r"_", "", data)
        data = re.sub(r"\s", "", data)

        data = re.sub(r"風溼", "風濕", data)
        data = re.sub(r"濕疹", "溼疹", data)
        data = re.sub(r"慢性老化性失智症", "慢性失智症", data)
        data = re.sub(r"敗血休克", "敗血性休克", data)
        data = re.sub(r"鬱血心衰竭", "鬱血性心衰竭", data)
        data = re.sub(r"急性缺氧呼吸衰竭", "急性缺氧性呼吸衰竭", data)
        data = re.sub(r"呼吸中止症", "呼吸中止症候群", data)
        data = re.sub(r"免疫低下", "免疫力低下", data)
        data = re.sub(r"瀰漫大B細胞淋巴瘤", "瀰漫性大B細胞淋巴瘤", data)

        data = re.sub(r"武漢肺炎", "新冠肺炎", data)
        data = re.sub(r"嚴重特殊傳染性疾病確診", "新冠肺炎", data)
        data = re.sub(r"乳腺惡性腫瘤", "乳腺癌", data)
        data = re.sub(r"大出血", "出血", data)

        data = data.replace("COVID19", "COVID-19")

        if data == "燒碳":
            data = "燒炭"
        if data == "洗腎":
            data = "腎衰竭"

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
            if "小客" in data:
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
            if "小客" in data or "汽車" in data:
                data = "車禍A21機車*汽車"
            elif "大貨車" in data:
                data = "車禍D3機車騎士*大貨車"
            elif "貨車" in data:
                data = "車禍A22機車*貨車"
            elif data.count("機車") == 2:
                data = "車禍A20機車"
        elif "自行車" in data or "腳踏車" in data:
            if "小客" in data or "汽車" in data:
                data = "車禍C2腳踏車騎士*汽車"
            elif "機車" in data:
                data = "車禍C1腳踏車騎士*機車"
            elif "摩托車" in data:
                data = "車禍C1腳踏車騎士*機車"
            elif "貨車" in data:
                data = "車禍C3腳踏車騎士*小貨車"

        return data

    def _is_subset(self, str1: str, str2: str) -> bool:
        if str1 == str2:
            return False
        for i in str1:
            if i not in str2:
                return False
        return True

    def remove_synonyms(self, data: list) -> list:
        result = []
        for d in data:
            if d in self.synonyms:
                if self.synonyms[d] not in result:
                    result.append(self.synonyms[d])
            else:
                result.append(d)
        return result

    def remove_subset(self, data: list) -> list:
        return [e for e in data if not any([self._is_subset(e, r) for r in data])]

    def remove_duplicate(self, data: list) -> list:
        return list(dict.fromkeys(data))

    def extract_icd(self, input_str: str):
        if input_str == "":
            return [""]
        input_str = self._pre_process(input_str)
        if self.trie.has_key(input_str):
            return [input_str]

        result = []
        while input_str != "":
            prefix = self.trie.longest_prefix(input_str).key
            if prefix is None:
                if self.experimental:
                    if self.trie.has_subtrie(input_str[0]):
                        possibles = [input_str[0]]
                        for ch in input_str[1:]:
                            currents = []
                            for poss in possibles:
                                if self.trie.has_node(poss + ch) != 0:
                                    currents.append(poss + ch)
                            possibles.extend(currents)
                        possibles = [e for e in possibles if self.trie.has_key(e)]
                        result.extend(possibles)
                input_str = input_str[1:]
            else:
                input_str = input_str.removeprefix(prefix)
                result.append(prefix)

        result = self.remove_subset(result)
        result = self.remove_synonyms(result)
        result = self.remove_duplicate(result)

        return result


if __name__ == "__main__":
    tokenizer = ICDTokenizer(experimental=True)
    tests = [
        "大腸直腸癌伴有肺部、肝臟轉移",
        "女性右側乳房未明示部位惡性腫瘤",
        "上葉之左側支氣管或肺惡性腫瘤",
        "右上肺葉惡性腫瘤",
        "子宮肌層肉瘤末期",
        "乳腺惡性腫瘤",
        "上消化道大出血",
        "心肺腎衰竭",
        "瀰漫大B細胞淋巴瘤",
        "手術修補 4.慢性腎衰竭經短期透析治療後5.高血壓 6.糖尿病7.院內死亡經急救後恢復心跳",
        "嚴重特殊傳染性肺炎(新冠肺炎)併呼吸衰竭",
        "老邁壽終",
    ]
    for string in tests:
        print(tokenizer.extract_icd(string))
