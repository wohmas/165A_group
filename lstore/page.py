
class Page:

    def __init__(self):
        self.num_records = 0
        self.data = []

    def has_capacity(self):
        pass

    def write(self, value):
        self.num_records += 1
        self.data.append(value)
        pass

