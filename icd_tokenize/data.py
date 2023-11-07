class Data(dict):
    KEYS = ["甲", "乙", "丙", "丁", "其他"]
    CODES = ["CA", "CB", "CC", "CD", "CE"]
    TAGS = ["", "2", "3", "4"]

    def __init__(self):
        super().__init__()
        self["甲"] = []
        self["乙"] = []
        self["丙"] = []
        self["丁"] = []
        self["其他"] = []
