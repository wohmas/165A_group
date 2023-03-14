"""
A data strucutre holding indices for various columns of a table. Key column should be indexd by default, other columns can be indexed through this object. Indices are usually B-Trees, but other data structures can be used as well.
"""
from BTrees.OOBTree import OOBTree
import threading


class Index:

    def __init__(self, table):
        # One index for each table. All our empty initially.
        self.table = table
        self.indices = [None for i in range(table.num_columns)]
        self.indices[0] = self.create_index(0)
        self.lock = threading.Lock()

    # insert new records
    # if key not unique, will overwrite old rid value
    def insert(self, rid, value, col):
        self.lock.acquire()
        if self.indices[col] == None:
            return
        vals = self.locate(col, value)
        vals.append(rid)
        # print("col: ", i, "value: ", value, "vals: ", vals)
        self.indices[col].update({value: vals})
        self.lock.release()

    def insert_all_existing_index(self, rid, values):
        i = 0
        for value in values:
            if self.indices[i] != None:
                self.insert(rid, value, i)
            i += 1
    """
    # returns the location of all records with the given value on column "column"
    """

    def locate(self, column, value):
        ret = None
        if self.indices[column] == None:
            return self.search_db(column, value, value)

        ret = list(self.indices[column].values(value, value))

        if len(ret) == 0:
            return ret
        return ret[0]

    """
    # Returns the RIDs of all records with values in column "column" between "begin" and "end"
    """

    def locate_range(self, begin, end, column):
        ret = None
        if self.indices[column] == None:
            return self.search_db(column, begin, end)
        bp_rids = list(self.indices[column].values(begin, end))
        ret = []
        for rids in bp_rids:
            if rids != []:
                ret.append(*rids)
        # print(ret)
        return ret

    def search_db(self, column_number, begin, end):
        bp_no = self.table.bp_num
        ret = []
        for bp in range(1, bp_no+1):
            pg = self.table.buffer_pool.return_page("b_"+str(bp))
            pg.pin()
            rec_no = pg.num_records()
            for i in range(rec_no):
                rid = pg.get_bp_rid(i)
                val = self.get_latest_val(pg, i, column_number)
                if val >= begin and val <= end:
                    ret.append(rid)
                pg.unpin()
        return ret

    def get_latest_val(self, pg, offset, column_number):
        if(pg.get_schema(offset)[column_number] == '0'):
            return pg.get_col_value(column_number, offset)

        indirection = pg.get_indirection(offset)
        # print(indirection)
        tail_page_id = self.table.page_directory[indirection][0]
        tail_record_offset = self.table.page_directory[indirection][1]
        tail_page = self.table.buffer_pool.return_page(tail_page_id)
        tail_page.pin()
        val = tail_page.get_col_value(column_number, tail_record_offset)
        tail_page.unpin()
        return val
    """
    # optional: Create index on specific column
    """

    def create_index(self, column_number):
        self.indices[column_number] = OOBTree()
        bp_no = self.table.bp_num
        for bp in range(1, bp_no+1):
            pg = self.table.buffer_pool.return_page("b_"+str(bp))
            pg.pin()
            rec_no = pg.num_records()
            for i in range(rec_no):
                rid = pg.get_bp_rid(i)
                val = self.get_latest_val(pg, i, column_number)
                pg.unpin()
                self.insert(rid, val, column_number)

    def remove(self, column, rid, value):
        if self.indices[column] == None:
            return
        self.indices[column].get(value).remove(rid)
    """
    # optional: Drop index of specific column
    """

    def drop_index(self, column_number):
        self.indices[column_number] = None
