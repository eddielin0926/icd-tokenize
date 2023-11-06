from icd_tokenize.icd import ICD


class ICDValidator:
    def __init__(self, icd: ICD = None) -> None:
        if icd is None:
            icd = ICD()
        self.synonyms = icd.synonyms

    def icd_validate(self, predict: list, target: list) -> bool:
        if "糖尿病" in predict and "腎臟病" in predict and "糖尿病腎臟病" in target:
            predict.remove("糖尿病")
            predict.remove("腎臟病")
            target.remove("糖尿病腎臟病")
        if "糖尿病" in target and "腎臟病" in target and "糖尿病腎臟病" in predict:
            target.remove("糖尿病")
            target.remove("腎臟病")
            predict.remove("糖尿病腎臟病")
        if "高血壓" in predict and "心臟病" in predict and "高血壓心臟病" in target:
            predict.remove("高血壓")
            predict.remove("心臟病")
            target.remove("高血壓心臟病")
        if "高血壓" in target and "心臟病" in target and "高血壓心臟病" in predict:
            target.remove("高血壓")
            target.remove("心臟病")
            predict.remove("高血壓心臟病")
        if "心肺腎衰竭" in predict and "心肺衰竭" in target and "腎衰竭" in target:
            predict.remove("心肺腎衰竭")
            target.remove("心肺衰竭")
            target.remove("腎衰竭")
        if "高血壓缺血性心臟病" in predict and "高血壓" in target and "缺血性心臟病" in target:
            predict.remove("高血壓缺血性心臟病")
            target.remove("高血壓")
            target.remove("缺血性心臟病")

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
