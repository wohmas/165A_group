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

class Table:

    """
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """
    def __init__(self, name, num_columns, key):
        self.name = name
        self.key = key
        self.num_columns = num_columns
        self.page_directory = {}
        self.bpnum = -1
        self.bp = self.bpcreate()
        self.index = Index(self)
        self.rid = 'bp0r0'
        pass
 
    def bpcreate(self):
        self.bpnum += 1
        return [Page() for i in range(self.num_columns + 2)]

    def bpwrite(self, values):
        for i in range(len(self.bp)):
            self.bp[i].write(values[i])

    def addpd(self, rid, locations):
        self.page_directory[rid] = locations

    def insert(self, values, schema):
        if not self.bp[0].has_capacity():
            self.bp = self.bpcreate()
        self.bpwrite([*values, schema, None])
        locations = [self.bp, self.bp[0].num_records]
        self.addpd(self.create_rid(), locations)
        # Add index insert once functional
        return True

    def create_rid(self):
        self.rid = f'bp{self.bpnum}r{self.bp[0].num_records}'
        return self.rid
    
    def __merge(self):
        print("merge is happening")
        pass
