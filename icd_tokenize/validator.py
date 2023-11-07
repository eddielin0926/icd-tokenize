from icd_tokenize.icd import ICD


class ICDValidator:
    def __init__(self, icd: ICD = None) -> None:
        if icd is None:
            icd = ICD()
        self.synonyms = icd.synonyms

    def icd_validate(self, predict: list, target: list) -> bool:
        combine_list = [
            ["高血壓", "心臟病", "高血壓心臟病"],
            ["糖尿病", "腎臟病", "糖尿病腎臟病"],
            ["糖尿病", "腎衰竭", "糖尿病腎衰竭"],
            ["高血壓", "缺血性心臟病", "高血壓缺血性心臟病"],
            ["高血壓", "心臟衰竭", "高血壓心臟衰竭"],
            ["心肺衰竭", "腎衰竭", "心肺腎衰竭"],
            ["敗血症", "休克", "敗血症休克"],
        ]
        for combine in combine_list:
            if combine[0] in predict and combine[1] in predict and combine[2] in target:
                predict.remove(combine[0])
                predict.remove(combine[1])
                predict.append(combine[2])
            elif combine[0] in target and combine[1] in target and combine[2] in predict:
                predict.append(combine[0])
                predict.append(combine[1])
                predict.remove(combine[2])

        for pred in predict:
            if not any([self._icd_compare(pred, tar) for tar in target]):
                return False
        for tar in target:
            if not any([self._icd_compare(pred, tar) for pred in predict]):
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
        if "末期" + str1 == str2 or str1 == "末期" + str2:
            return True
        if str1 + "病史" == str2 or str1 == str2 + "病史":
            return True
        return False


if __name__ == "__main__":
    validator = ICDValidator()
    predict = ["高血壓心臟病", "糖尿病", "腎臟病", ""]
    target = ["高血壓", "心臟病", "糖尿病腎臟病", ""]
    print(validator.icd_validate(predict, target))
