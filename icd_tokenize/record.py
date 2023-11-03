from dataclasses import dataclass, field


@dataclass
class Record:
    year: int
    month: int
    serial: int
    number: int
    is_correct: bool = field(default=False)
    inputs: dict[str, list[str]] = field(default_factory=dict)
    tokens: dict[str, list[str]] = field(default_factory=dict)
    keys = {
        "甲": "CA",
        "乙": "CB",
        "丙": "CC",
        "丁": "CD",
        "其他": "CE",
    }

    def for_json(self):
        result = {
            "資料鍵入年": str(self.year),
            "資料鍵入月": str(self.month).zfill(2),
            "死因自動流水號": str(self.serial).zfill(6),
        }

        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            if len(self.tokens[catalog]) < 4:
                self.tokens[catalog] += ["" for _ in range(4 - len(self.tokens[catalog]))]
            for i in range(4):
                result[f"{self.keys[catalog]}{i + 1}"] = self.tokens[catalog][i]

        return result

    def for_excel(self):
        result = {
            "s_num": self.serial,
            "NO": self.number,
            "斷詞前": None,
        }

        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            if len(self.inputs[catalog]) < 4:
                self.inputs[catalog] += ["" for _ in range(4 - len(self.inputs[catalog]))]
            for i, tag in enumerate(["", "2", "3", "4"]):
                result[f"{catalog}{tag}"] = self.inputs[catalog][i]

        result["斷詞後"] = None

        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            if len(self.tokens[catalog]) < 4:
                self.tokens[catalog] += ["" for _ in range(4 - len(self.tokens[catalog]))]
            for i, tag in enumerate([".1", "2.1", "3.1", "4.1"]):
                result[f"{catalog}{tag}"] = self.tokens[catalog][i]
        return result
