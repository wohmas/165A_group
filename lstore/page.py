
class Page:

    def __init__(self, r_num, data):
        self.num_records = r_num
        self.data = self.get_data(data)
        
    def get_data(self, data):
        if data == -1:
            return bytearray(4096)
        else:
            return bytearray(data)
    
    def getAll(self):
        return self.data
    def has_capacity(self):
        return (self.num_records < 512)
    
    def get_int(self, rec_num):
        num_bytes = self.data[rec_num*8:rec_num*8+8]
        return int.from_bytes(num_bytes, "little")

    def get_str(self, rec_num):
        str_bytes = self.data[rec_num*8:rec_num*8+8].copy()
        return str_bytes.decode("utf-8").replace('\00','')

    def update_int(self, value, rec_num):
        bytes = list((value >> i) & 0xFF for i in range(0,64,8))
        self.write_to_data(bytes, rec_num)

    def update_str(self, str, rec_num):
        bytes = str.encode('utf-8')
        self.write_to_data(bytes, rec_num)
        
    def write_to_data(self, bytes, rec_num):
        count = 0
        for i in bytes:
            self.data[rec_num*8+count] = i
            count+=1

    def write(self, value):
        if (value == None):
            self.num_records += 1
            return
        bytes = []
        if (isinstance(value, int)):    
            bytes = list((value >> i) & 0xFF for i in range(0,64,8))
        else:
            bytes = value.encode('utf-8')
        self.write_to_data(bytes, self.num_records)
        self.num_records += 1
        