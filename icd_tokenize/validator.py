from icd_tokenize.data import Data
from icd_tokenize.icd import ICD
from icd_tokenize.status import Status


class ICDValidator:
    def __init__(self, icd: ICD = None) -> None:
        if icd is None:
            icd = ICD()
        self.synonyms = icd.synonyms

    def identical_icd(self, predicts: Data, targets: Data) -> Status:
        data = Status()
        for catalog in Data.KEYS:
            data[catalog] = set(predicts[catalog]) == set(targets[catalog])
        return data

    def validate_icd(self, predicts: Data, targets: Data) -> Status:
        data = Status()
        for catalog in Data.KEYS:
            data[catalog] = self.validate(predicts[catalog], targets[catalog])
        return data

    def validate(self, predict: list, target: list) -> bool:
        combine_list = [
            ["高血壓", "心臟病", "高血壓心臟病"],
            ["高血壓病史", "心臟病", "高血壓心臟病"],
            ["高血壓", "心血管疾病", "高血壓心血管疾病"],
            ["高血壓心臟病", "衰竭", "高血壓心臟病衰竭"],
            ["高血壓心臟病", "心衰竭", "高血壓心臟病衰竭"],
            ["高血壓心臟病", "心臟衰竭", "高血壓心臟病衰竭"],
            ["糖尿病", "腎臟病", "糖尿病腎臟病"],
            ["糖尿病", "腎衰竭", "糖尿病腎衰竭"],
            ["糖尿病", "慢性腎病變", "糖尿病慢性腎病變"],
            ["糖尿病", "末期腎病", "糖尿病末期腎病變"],
            ["糖尿病", "末期腎病變", "糖尿病末期腎病變"],
            ["高血壓", "缺血性心臟病", "高血壓缺血性心臟病"],
            ["高血壓", "心臟衰竭", "高血壓心臟衰竭"],
            ["高血壓心臟病", "心臟衰竭", "高血壓心臟病衰竭"],
            ["心肺衰竭", "腎衰竭", "心肺腎衰竭"],
            ["敗血症", "休克", "敗血症休克"],
            ["乳癌", "轉移", "乳癌轉移"],
            ["大腸癌", "轉移", "大腸癌轉移"],
            ["癌症末期", "惡病質", "癌症末期惡病質"],
            ["胰臟癌", "多處轉移", "胰臟癌多處轉移"],
        ]
        for pred in predict:
            if not any([self._icd_compare(pred, tar) for tar in target]):
                special_case = False
                for c in combine_list:
                    if pred == c[0] and c[1] in predict and c[2] in target:
                        special_case = True
                        break
                    elif c[0] in predict and pred == c[1] and c[2] in target:
                        special_case = True
                        break
                    elif pred == c[2] and c[0] in target and c[1] in target:
                        special_case = True
                        break
                if not special_case:
                    return False
        for tar in target:
            if not any([self._icd_compare(pred, tar) for pred in predict]):
                special_case = False
                for c in combine_list:
                    if tar == c[0] and c[1] in target and c[2] in predict:
                        special_case = True
                        break
                    elif c[0] in target and tar == c[1] and c[2] in predict:
                        special_case = True
                        break
                    elif tar == c[2] and c[0] in predict and c[1] in predict:
                        special_case = True
                        break
                if not special_case:
                    return False
        return True

    def _icd_compare(self, str1: str, str2: str) -> bool:
        str1, str2 = str1.upper(), str2.upper()
        if str1 == str2:
            return True
        if str1 in self.synonyms and str2 in self.synonyms:
            return self.synonyms[str1] == self.synonyms[str2]
        if str1 + "死亡" == str2 or str1 == str2 + "死亡":
            return True
        if str1 + "復發" == str2 or str1 == str2 + "復發":
            return True
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
