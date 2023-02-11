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
        self.bp_num = -1
        self.tp_num = -1
        self.bp = self.bpcreate()
        self.index = Index(self)
        pass

    def bpcreate(self):
        self.bp_num += 1
        return [Page() for i in range(self.num_columns + 2)]

    def bpwrite(self, values):
        for i in range(len(self.bp)):
            self.bp[i].write(values[i])

    def addpd(self, rid, locations):
        self.page_directory[rid] = locations

    def insert(self, values, schema):
        if not self.bp[0].has_capacity():
            self.bp = self.bpcreate()
        rid = self.create_rid("bp")
        self.bpwrite([*values, schema, ""])
        locations = [self.bp, self.bp[0].num_records-1]
        self.addpd(rid, locations)
        self.index.insert(rid, values[0])
        print("page_dir : ", self.page_directory)
        print()
        return True

    def create_rid(self, pg_type):
        pg_num = 0
        if pg_type == 'bp':
            pg_num = self.bp_num
        else:
            pg_num = self.tp_num

        return f'{pg_type}{pg_num}r{self.bp[0].num_records}'

    def __merge(self):
        print("merge is happening")
        pass
