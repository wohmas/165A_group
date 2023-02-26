from lstore.index import Index
from time import time
from lstore.page import Page

INDIRECTION_COLUMN = 0
RID_COLUMN = 1
TIMESTAMP_COLUMN = 2
SCHEMA_ENCODING_COLUMN = 3


class Record:

    def __init__(self, rid, key, columns):
        self.rid = rid
        self.key = key
        self.columns = columns

    def print_record(self):
        print("RID: " + str(self.rid) + " KEY: " +
              str(self.key) + " VALUES: " + str(self.columns))


class PageGrp:
    def __init__(self, id, rel_path, num_col):
        self.id = id
        self.isDirty = False
        self.isPinned = False
        self.rel_path = rel_path+"/pg_"+self.id+".txt"
        self.pin_count = 0
        self.pages = self.read_from_file()

    def pg_write(self, values):
        self.isPinned = True
        self.pin_count += 1
        self.isDirty = True
        for i in range(len(self.pages)):
            self.pages[i].write(values[i])
        self.isPinned = False

    def get_col_values(self, record_no, projected_columns_index):
        self.isPinned = True
        self.pin_count += 1
        values = []
        for i in range(0, len(projected_columns_index)):
            if projected_columns_index[i] == 1:
                values.append(self.pages[i].get_int(record_no))
            else:
                values.append(None)
        self.isPinned = False
        return values

    def write_to_file(self):
        self.isPinned = True
        self.pin_count += 1
        with open(self.rel_path, "wb") as file:
            for page in self.pages:
                file.write(page.getAll())
        self.isPinned = False

    def read_from_file(self):
        self.isPinned = True
        self.pin_count += 1
        page_list = []
        with open(self.rel_path, "rb") as file:
            byte = file.read(4096)
            while byte:
                page_list.append(Page(byte))
        self.isPinned = False
        return page_list
    
    def get_pin_count(self):
        return self.pin_count


class BufferPool:
    def __init__(self, path, num_col):
        self.files_in_mem = 0
        self.next_to_eject = None
        self.pages_in_mem = {}  # key: id, Value: PageGrp object
        self.path = path
        self.num_col = num_col

    def add_page(self, id):
        if self.files_in_mem == 16:
            self.rem_page(self, id)

        # assuming buffer pool has space
        self.pages_in_mem[id] = PageGrp(id, self.path, self.num_col)
        
        self.files_in_mem += 1  # should max out at 16

    def rem_page(self, id):
        for key in self.pages_in_mem:
            if self.pages_in_mem[key].isPinned == False:
                lowest = self.pages_in_mem[key].pin_count
                break

        for key in self.pages_in_mem:
            if self.pages_in_mem[key].pin_count < lowest and self.pages_in_mem[key].isPinned == False:
                lowest = key

        if self.pages_in_mem[lowest].isDirty == True:
            self.pages_in_mem[lowest].write_to_file()

        
        # 1) Remove lowest from dictionary 
        # 2) Delete the object itself 
        # 3) Create a new pagegroup object w/ id, path, num_cols arguments
        # 4) Read from file 
        # 5) Insert into dictionary     
     
        # to be called in add page if buffer pool is full
        # logic to eject a page