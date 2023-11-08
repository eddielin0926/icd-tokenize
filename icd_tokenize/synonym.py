import os

import pandas as pd


class Synonym(dict):
    def __init__(self, dir_path: str = None) -> None:
        """Initialize synonym dictionary."""
        super().__init__()
        if dir_path is None:
            dir_path = os.path.join(os.path.dirname(__file__), "data")

        synonym_file = os.path.join(dir_path, "synonym.csv")
        df = pd.read_csv(synonym_file)
        for _, row in df.iterrows():
            icd = row["ICD1"]
            synonyms = row["diagnosis"]
            self[synonyms] = icd
