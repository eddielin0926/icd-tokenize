class Status(dict):
    def __init__(self):
        super().__init__()
        self["甲"] = False
        self["乙"] = False
        self["丙"] = False
        self["丁"] = False
        self["其他"] = False
