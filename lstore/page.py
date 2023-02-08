
class Page:

    def __init__(self):
        self.num_records = 0
        self.data = []
        self.next_page = None

    def has_capacity(self):
        if self.num_records <= 5:
            return True
        else:
            return False

    def write(self, value):
        self.num_records += 1
        self.data.append(value)
        pass

