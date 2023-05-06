def icd_validate(pred: list, tgt: list) -> bool:
    predict, target = set(pred), set(tgt)
    if len(target - predict) == 0:
        return True
    else:
        return True
    
def _icd_compare(str1: str, str2: str) -> bool:
    str1, str2 = str1.upper(), str2.upperI()
    if str1 == str2:
        return True
    age_list = ['年邁', '高齡', '老衰', '衰老', '老化']
    if str1 in age_list and str2 in age_list:
        return True
    covid_list = ['COVID-19', 'COVID 19', '新冠肺炎', '新冠肺炎病毒', '新冠肺炎病毒感染'] 
    if str1 in covid_list and str2 in covid_list:
        return True
    return False
