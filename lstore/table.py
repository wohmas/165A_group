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
        self.tp = self.pg_create("tp")
        self.bp = self.pg_create("bp")
        self.index = Index(self)
        pass

    def pg_create(self, type):
        if type == "bp":
            self.bp_num += 1
        else:
            self.tp_num += 1
        return [Page() for i in range(self.num_columns + 2)]

    def pg_write(self, pg, values):
        for i in range(len(pg)):
            pg[i].write(values[i])

    def addpd(self, rid, locations):
        self.page_directory[rid] = locations


    def update(self, key, cols):
        if not self.tp[0].has_capacity():
            self.tp = self.pg_create("tp")
        tp_rid = self.create_rid("tp")
        bp_rid = self.index.locate(0, key)
        record_bp = self.page_directory[bp_rid[0]]
        indirection = record_bp[0][-1].get_str(record_bp[1])#to put in tp
        record_bp[0][-1].update_str(tp_rid, record_bp[1])
        new_schema = ''.join('0' if val is None else '1' for val in cols)
        last_schema = record_bp[0][-2].get_str(record_bp[1])
        print()

        last_update_record =  self.page_directory[indirection]
        for i in range(0,len(last_schema)):
            if(last_schema[i] == 1 and cols[i]==None):
                new_schema[i] = "1"
                cols[i] = last_update_record[0][i].get_int(last_update_record[1])
        
        record_bp[0][-2].update_str(new_schema, record_bp[1])
        self.pg_write(self.tp, [*cols, new_schema, indirection])
        locations = [self.tp, self.tp[0].num_records-1]
        self.addpd(tp_rid, locations)

    def print_pg(self):
        for i in self.page_directory.keys():
            print("rid : ", i)
            # print(self.page_directory[i][0])
            for j in range(0, len(self.page_directory[i][0])-2):
                print(f"col {j}: ",self.page_directory[i][0][j].get_int(self.page_directory[i][1]))
            print("schema : ", self.page_directory[i][0][-2].get_str(self.page_directory[i][1]))

            print("indirection : ", self.page_directory[i][0][-1].get_str(self.page_directory[i][1]))
            print("======================================================")  
         

            

    def insert(self, values, schema):
        if not self.bp[0].has_capacity():
            self.bp = self.pg_create("bp")
        rid = self.create_rid("bp")
        self.pg_write(self.bp, [*values, schema, rid])
        locations = [self.bp, self.bp[0].num_records-1]
        self.addpd(rid, locations)
        self.index.insert(rid, values[0])
        # print("page_dir : ", self.page_directory)
        # print()
        return True

    def create_rid(self, pg_type):
        if pg_type == 'bp':
            return f'bp{self.bp_num}r{self.bp[0].num_records}'
        else:
            return f'tp{self.tp_num}r{self.tp[0].num_records}'

        

    # for primary keys for now     
    #
    # def read(self, search_key, search_key_index, projected_columns_index, relative_version):
    #   rids = self.index.locate(self, search_key_index, search_key)
    #   
    #   for (int i in range(0, length(rids))): 
    #       if rids[i][1] == 'b'
    #
    #   \\sort through rids to find the latest version 
    #   \\maybe find the base page rid, go to it, and use indirection for latest
    #   
    #
    #   location = self.page_directory[latest_rid] 
    #   indirect_rid = location[0][-1].get_int(location[1])  <-reads indirection page and stores the rid
    #
    #   for (i in range(0, abs(relative_version))):
    #       \\use indirection to go to last tail page
    #       \\store as new location
    #       location = self.page_directory[indirect_rid] <- ith indirected column
    #       indirect_rid = location[0][-1].get_int(location[1]) <- rid of i + 1th column
    #       \\continue until we have reached desired record version and have it in location
    #   
    #   \\read latest version of record 
    #   values = [] <- list store column values
    #   for (i in range(0, self.num_columns)):
    #       if (projected_columns_index[i] == 1):
    #           values.append(location[0][i].get_int(location[1]))
    #       else:
    #           values.append(None) \\assuming we don't want to just leave it empty
    #
    #   \\create record object    
    #   rid = location[0][-1].get_int(location[1]) 
    #   key = ??
    #   columns = values
    #   r = Record(rid, key, columns) 
    #        

    def __merge(self):
        print("merge is happening")
        pass
