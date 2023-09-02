class ICDValidator:
    def __init__(self, path="icd/synonyms.txt") -> None:
        with open(path, "r", encoding="utf-8") as f:
            self.synonyms_list = []
            for line in f.readlines():
                line = line.replace("\n", "")
                self.synonyms_list.append(line.split(","))

    def icd_validate(self, predict: list, target: list) -> bool:
        predict = [predict[i : i + 4] for i in range(0, len(predict), 4)]
        target = [target[i : i + 4] for i in range(0, len(target), 4)]
        for pred, trgt in zip(predict, target):
            pred = sorted(pred)
            trgt = sorted(trgt)
            for str1, str2 in zip(pred, trgt):
                if not self._icd_compare(str1, str2):
                    return False
        return True

    def _icd_compare(self, str1: str, str2: str) -> bool:
        str1, str2 = str1.upper(), str2.upper()
        if str1 == str2:
            return True
        for synonym in self.synonyms_list:
            if str1 in synonym and str2 in synonym:
                return True
        return False
