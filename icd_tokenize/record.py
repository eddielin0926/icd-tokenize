from dataclasses import dataclass, field

from icd_tokenize.data import Data
from icd_tokenize.status import Status


@dataclass
class Record:
    """
    Store result of each tokenized data
    """

    year: int
    month: int
    serial: int
    number: int
    identical: Status = field(default_factory=dict)
    corrects: Status = field(default_factory=dict)
    inputs: Data = field(default_factory=lambda: Data())
    results: Data = field(default_factory=lambda: Data())
    targets: Data = field(default_factory=lambda: Data())

    @property
    def is_correct(self):
        """Return True if all results are correct"""
        return all(self.corrects.values())

    @property
    def is_identical(self):
        """Return True if all results are identical to all targets"""
        return all(self.identical.values())

    @property
    def dirty(self):
        """Return the number of inputs that contains '?'"""
        count = 0
        for data in self.inputs.values():
            if any(["?" in d for d in data]):
                count += 1
        return count

    def for_json(self):
        """Return dict for json output"""
        data = {
            "資料鍵入年": str(self.year),
            "資料鍵入月": str(self.month).zfill(2),
            "死因自動流水號": str(self.serial).zfill(6),
        }

        for catalog, code in enumerate(Data.KEYS, Data.CODES):
            if len(self.results[catalog]) < 4:
                self.results[catalog] += ["" for _ in range(4 - len(self.results[catalog]))]
            for i in range(4):
                data[f"{code}{i + 1}"] = self.results[catalog][i]

        return data

    def for_excel(self):
        """Return dicts for excel output"""
        index = {"s_num": self.serial, "NO": self.number}
        before = {}
        after = {}

        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            if len(self.inputs[catalog]) < 4:
                self.inputs[catalog] += ["" for _ in range(4 - len(self.inputs[catalog]))]

            if len(self.results[catalog]) < 4:
                self.results[catalog] += ["" for _ in range(4 - len(self.results[catalog]))]

            for i, tag in enumerate(["", "2", "3", "4"]):
                before[f"{catalog}{tag}"] = self.inputs[catalog][i]
                after[f"{catalog}{tag}"] = self.results[catalog][i]

        return index, before, after

    def get_errors(self):
        """Return error data for csv output"""
        errors = []
        for catalog in ["甲", "乙", "丙", "丁", "其他"]:
            data = {"serial": self.serial, "catalog": catalog}
            if not self.corrects[catalog]:
                data["inputs"] = list(filter(None, self.inputs[catalog]))
                data["results"] = list(filter(None, self.results[catalog]))
                data["targets"] = list(filter(None, self.targets[catalog]))
                errors.append(data)
        return errors
