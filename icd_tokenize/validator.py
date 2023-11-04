from icd_tokenize.icd import ICD


class ICDValidator:
    def __init__(self, icd: ICD = None) -> None:
        if icd is None:
            icd = ICD()
        self.synonyms = icd.synonyms

    def icd_validate(self, predict: list, target: list) -> bool:
        predict, target = sorted(predict), sorted(target)
        for pred, trgt in zip(predict, target):
            if not self._icd_compare(pred, trgt):
                return False
        return True

    def _icd_compare(self, str1: str, str2: str) -> bool:
        str1, str2 = str1.upper(), str2.upper()
        if str1 == str2:
            return True
        if str1 in self.synonyms and str2 in self.synonyms:
            return self.synonyms[str1] == self.synonyms[str2]
        if str1 + "疾病" == str2 or str1 == str2 + "疾病":
            return True
        if str1 + "術後" == str2 or str1 == str2 + "術後":
            return True
        if str1 + "末期" == str2 or str1 == str2 + "末期":
            return True
        if str1 + "病史" == str2 or str1 == str2 + "病史":
            return True
        return False


if __name__ == "__main__":
    validator = ICDValidator()
    predict = ["肝臟轉移", "大腸直腸癌", "肺部轉移"]
    predict.sort(key=lambda s: len(s), reverse=True)
    print(predict)
    target = ["大腸直腸癌", "肺部轉移", "肝臟轉移"]
    print(validator.icd_validate(predict, target))
