
class Page:

    def __init__(self):
        self.num_records = 0
        self.data = bytearray(16)

    def has_capacity(self):
        return (self.num_records < 512)
    
    def get_int(self, rec_num):
        num_bytes = self.data[rec_num*8:rec_num*8+8]
        return int.from_bytes(num_bytes, "little")

    def get_str(self, rec_num):
        str_bytes = self.data[rec_num*8:rec_num*8+8].copy()
        print("in str")
        return str_bytes.decode("utf-8")

    def update_str(self, str, rec_num):
        print("in update")
        bytes = str.encode('utf-8')
        print(bytes)
        self.write_to_data(bytes, rec_num)

    def write_to_data(self, bytes, rec_num):
        count = 0
        for i in bytes:
            self.data.insert(rec_num*8+count,i)
            count+=1
        print(self.data)

    def write(self, value):
        
        bytes = []
        if (isinstance(value, int)):    
            bytes = list((value >> i) & 0xFF for i in range(0,64,8))
        else:
            bytes = value.encode('utf-8')
        self.write_to_data(bytes, self.num_records)
        self.num_records += 1
        