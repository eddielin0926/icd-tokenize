import numpy as np


class ICDValidator:
    def __init__(self, path='icd/synonyms.txt') -> None:
        with open(path, 'r', encoding="utf-8") as f:
            self.synonyms_list = []
            for line in f.readlines():
                self.synonyms_list.append(line.split(','))

    def icd_validate(self, predict: list, target: list) -> bool:
        predict = [predict[i: i+4] for i in range(0, len(predict), 4)]
        target = [target[i: i+4] for i in range(0, len(target), 4)]
        for pred, trgt in zip(predict, target):
            for str1 in pred:
                if str1 == '':
                    continue
                exist = False
                for str2 in trgt:
                    if str2 == '':
                        continue
                    if self._icd_compare(str1, str2):
                        exist = True
                        break
                if not exist:
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


if __name__ == '__main__':
    validator = ICDValidator()

    predict = ['Covid-19', '', '', '', '新冠肺炎', '', '', '', 'COVID-19',
               '', '', '', 'COVID 19', '', '', '', '新冠肺炎病毒', '', '', '']
    target = ['COVID-19', '', '', '', 'COVID-19', '', '', '', 'COVID-19',
              '', '', '', 'COVID-19', '', '', '', 'COVID-19', '', '', '']

    print(validator.icd_validate(predict, target))
