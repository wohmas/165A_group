
class Page:

    def __init__(self):
        self.num_records = 0
        self.data = bytearray(4096)

    def has_capacity(self):
        return True 
     #   try:
      #      self.data.index(0)
     #       return True
     #   except:
     #       return False

    def write(self, value):
        self.num_records += 1
        # address = self.data.index(0)
        # self.data[address] = value

