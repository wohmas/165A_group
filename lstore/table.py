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
        print("RID: " + str(self.rid) + " KEY: " + str(self.key) + " VALUES: " + str(self.columns))    


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
        indirection = record_bp[0][-1].get_str(record_bp[1])
        record_bp[0][-1].update_str(tp_rid, record_bp[1])
        new_schema = ''.join('0' if val is None else '1' for val in cols)
        last_schema = record_bp[0][-2].get_str(record_bp[1])
        val = list(cols)
        last_update_record =  self.page_directory[indirection]
        for i in range(0,len(last_schema)):
            if(last_schema[i] == '1' and cols[i]==None):
                new_schema = new_schema[:i] + "1" + new_schema[i+1:]
                val[i] = last_update_record[0][i].get_int(last_update_record[1])
        record_bp[0][-2].update_str(new_schema, record_bp[1])
        self.pg_write(self.tp, [*val, new_schema, indirection])
        locations = [self.tp, self.tp[0].num_records-1]
        self.addpd(tp_rid, locations)

    def print_pg(self):
        for i in self.page_directory.keys():
            print("rid : ", i)
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

        

    # only for primary keys for now     
    #
    def read(self, search_key, search_key_index, projected_columns_index, relative_version):
        
        base_rid = self.index.locate(search_key_index, search_key)
        # print(base_rid[0])

    #   this is the base rid
    #   find base page, and get its indirection column 
        base_location = self.page_directory[base_rid[0]] 
        latest_rid = base_location[0][-1].get_str(base_location[1])
        # print(latest_rid)

    #   now go to latest tail page
        tail_location = self.page_directory[latest_rid] 
    #
        for i in range(0, abs(relative_version)):
    #       use indirection to go to last tail page
    #       store as new location
            indirect_rid = tail_location[0][-1].get_str(tail_location[1]) # <- rid of i + 1th column
            # print(indirect_rid)
            tail_location = self.page_directory[indirect_rid] # <- ith indirected column
    #       continue until we have reached desired record version and have it in location
       
    #   read latest version of record 
    #   refers to schema so it knows whether to enforce base page or tail page
        values = [] # <- list to store column values
        # print("Proj Col = " + str(len(projected_columns_index)))
        Schema = tail_location[0][-2].get_str(tail_location[1])
        # print("Schema = " + tail_location[0][-2].get_str(tail_location[1]))
        for i in range(0, len(projected_columns_index)):
            if projected_columns_index[i] == 1:
                # print(Schema[i])    
                if Schema[i] == str(1):
                    # print("IF BRANCH CHOSEN")
                    values.append(tail_location[0][i].get_int(tail_location[1]))
                    # print(tail_location[0][i].get_int(tail_location[1]))
                else:
                    # print("ELSE BRANCH CHOSEN")
                    values.append(base_location[0][i].get_int(base_location[1]))
                    # print(base_location[0][i].get_int(base_location[1]))    
            else:
                values.append(None) # assuming we don't want to just leave it empty
                # print(None)

    #   create record object    
        r = Record(tail_location[0][-1].get_str(tail_location[1]), search_key, values)
        r.print_record() 
        return r        

    def __merge(self):
        print("merge is happening")
        pass
