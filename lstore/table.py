from lstore.index import Index
from time import time
from lstore.page import Page
import os
import math

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
        self.num_col = num_col
        self.isPinned = False
        self.rel_path = "pg_"+self.id+".txt"
        self.pages = self.read_from_file()

    def get_id(self):
        return self.id

    def pg_write(self, values):
        self.isDirty = True
        for i in range(len(self.pages)):
            self.pages[i].write(values[i])

    def get_col_values(self, record_no, projected_columns_index):
        values = []
        for i in range(0, len(projected_columns_index)):
            if projected_columns_index[i] == 1:
                values.append(self.pages[i].get_int(record_no))
            else:
                values.append(None)
        return values

    # def get_col_value(self, num, offset):
    #     return self.pages[num].get_int(offset)

    def write_to_file(self):
        with open(self.rel_path, "wb") as file:
            rec_num = self.pages[0].num_records.to_bytes(8, "little")
            file.write(rec_num)
            for page in self.pages:
                file.write(page.getAll())

    def read_from_file(self):
        page_list = []
        try:
            with open(self.rel_path, "rb") as file:
                rec_num = file.read(8)
                r = int.from_bytes(rec_num, "little")

                while True:
                    bytes = file.read(32)
                    # print(bytes)
                    if not bytes:
                        break
                    page_list.append(Page(r, bytes))
                    # print("================================")

        except:
            # print("file does not exists")
            page_list = [Page(0, -1) for i in range(self.num_col+2)]
        return page_list

    def print_contents(self, offset):
        vals = self.get_col_values(offset, [1 for _ in range(self.num_col)])
        print(f"columns : {vals}")
        print(f"schema: {self.get_schema(offset)}")
        print(f"indirection: {self.get_indirection(offset)}")

    # so table does not directly interact with page objects
    def has_capacity(self):
        return self.pages[0].has_capacity()

    def num_records(self):
        return self.pages[0].num_records

    def get_indirection(self, offset):
        return self.pages[-1].get_int(offset)

    def update_indirection(self, value, offset):
        self.pages[-1].update_int(value, offset)

    def get_schema(self, offset):
        return self.pages[-2].get_str(offset)

    def update_schema(self, schema, offset):
        return self.pages[-2].update_str(schema, offset)

    def pin(self):
        self.isPinned = True

    def unpin(self):
        self.isPinned = False


class BufferPool:
    def __init__(self, path, num_col):
        self.files_in_mem = 0
        self.next_to_eject = None
        self.pages_in_mem = {}  # key: id, Value: PageGrp object
        self.path = path
        self.num_col = num_col

    # to be called in add page if buffer pool is full
    # page ejection
    def rem_page(self):
        # currently assumes no scenario where all pages are pinned
        # in milestone 3 this assumption will not hold and we will need more conditions
        # print("in rem")
        for id in self.pages_in_mem.keys():
            if self.pages_in_mem[id].isDirty == False and self.pages_in_mem[id].isPinned == False:
                del self.pages_in_mem[id]
                self.files_in_mem -= 1
                break

        for id in self.pages_in_mem.keys():
            if self.pages_in_mem[id].isDirty == True and self.pages_in_mem[id].isPinned == False:
                self.pages_in_mem[id].write_to_file()
                del self.pages_in_mem[id]
                self.files_in_mem -= 1
                break

    def add_page(self, id):
        if self.files_in_mem >= 3:
            self.rem_page()

        # assuming buffer pool has space
        self.pages_in_mem[id] = PageGrp(id, self.path, self.num_col)
        self.files_in_mem += 1  # should max out at 16

    # table getter
    def return_page(self, id):
        if self.pages_in_mem.get(id) == None:
            self.add_page(id)

        return self.pages_in_mem.get(id)


class Table:

    """
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def __init__(self, name, num_columns, key):
        # recieve database path, create tail page path by appending name to it
        self.name = name
        self.key = key
        self.num_columns = num_columns
        self.page_directory = {}
        self.nums = 0
        self.page_num = 0
        self.page_range_map = {}
        self.bp_num = 0
        self.tp_num = 0
        self.latest_bp_id = self.create_pid("b")
        self.index = Index(self)
        self.buffer_pool = BufferPool(name, num_columns)

    # now irrelevant because pgroup handles this?
    def get_tail_pg(self, bp_id):
        bp_id = int(bp_id[1:])
        print("bp_id: ", bp_id)
        grp = math.ceil(bp_id/2)
        print("grp: ", grp)

        if grp not in self.page_range_map.keys():
            self.page_range_map[grp] = self.create_pid("t")
        tp_id = self.page_range_map[grp]
        tail_page = self.buffer_pool.return_page(tp_id)
        tail_page.pin()
        # if full, create new tail page ID
        # by requesting the page bufferpool (should) automatically create it
        if tail_page.has_capacity() == False:

            tp_id = self.create_pid("t")
            self.page_range_map[grp] = tp_id
            tail_page.unpin()
            tail_page = self.buffer_pool.return_page(tp_id)
            tail_page.pin()
        print("tp_id: ", tp_id)
        print("================================")
        return tail_page

    def pg_write(self, pg, values):
        for i in range(len(pg)):
            pg[i].write(values[i])

    # locations will now just be base/page id, along with offset etc.
    def addpd(self, rid, locations):
        self.page_directory[rid] = locations

    def update(self, key, cols):

        # use index to get base rid related to key
        # find basepage ID from page directory
        bp_rid = self.index.locate(0, key)[0][0]
        # find basepage ID from page directory
        bp_id = self.page_directory[bp_rid][0]
        base_offset = self.page_directory[bp_rid][1]
        # get basepage from bufferpool using ID
        base_page = self.buffer_pool.return_page(bp_id)
        base_page.pin()

        # ask bufferpool for latest tail page
        tail_page = self.get_tail_pg(bp_id)
        tail_page.pin()

        # if full, create new tail page ID
        # by requesting the page bufferpool (should) automatically create it

        tp_rid = self.create_rid()

        # get rid from base indirection column via pagegroup
        indirection = base_page.get_indirection(base_offset)
        # update indirection value of base record via pagegroup
        base_page.update_indirection(tp_rid, base_offset)
        # generate schema for updated columns
        new_schema = ''.join('0' if val is None else '1' for val in cols)
        # get schema from base record via pagegroup
        last_schema = base_page.get_schema(base_offset)
        # Make input cols mutable
        val = list(cols)
        # use old indirection value (first step of this block) to get corresponding page directory ID
        last_update_record_id = self.page_directory[indirection][0]
        last_update_record_offset = self.page_directory[indirection][1]
        # use bufferpool to get corresponding pagegroup object
        last_update_record = self.buffer_pool.return_page(
            last_update_record_id)

        # recreate for loop w/ appropiate pagegroup references
        for i in range(0, len(last_schema)):
            projected_index = [None for i in range(self.num_columns)]
            if(last_schema[i] == '1' and cols[i] == None):
                new_schema = new_schema[:i] + "1" + new_schema[i+1:]
                projected_index[i] = 1
                val[i] = last_update_record.get_col_values(
                    last_update_record_offset, projected_index)[i]

        # ..go from there
        base_page.update_schema(new_schema, base_offset)
        # hopefully this works
        tail_page.pg_write([*val, new_schema, indirection])
        locations = [tail_page.get_id(), tail_page.num_records() - 1]
        tail_page.unpin()
        base_page.unpin()
        self.addpd(tp_rid, locations)

    # STILL NOT UPDATED FOR BUFFERPOOL

    def print_pg(self):
        '''For Internal use: prints all RIDs and their values found in page directory'''
        for i in self.page_directory.keys():
            print("rid : ", i)
            pg = self.buffer_pool.return_page(self.page_directory[i][0])
            pg.print_contents(self.page_directory[i][1])
            print("======================================================")

    def insert(self, values, schema):
        # ask bufferpool for newest base page
        # call has_capacity on page_group
        base_page = self.buffer_pool.return_page(self.latest_bp_id)
        base_page.pin()
        # if full, create new base page ID
        # by requesting the page bufferpool (should) automatically create it
        if base_page.has_capacity() == False:
            print("in has cap false")
            self.latest_bp_id = self.create_pid("b")
            base_page.unpin()
            base_page = self.buffer_pool.return_page(self.latest_bp_id)
            base_page.pin()

        rid = self.create_rid()
        # write values to base page
        base_page.pg_write([*values, schema, rid])
        # update page directory and index
        locations = [base_page.get_id(), base_page.num_records() - 1]
        base_page.unpin()
        self.index.insert(rid, values)
        self.addpd(rid, locations)
        return True

    def create_rid(self):
        self.nums += 1
        return self.nums

    def create_pid(self, type):
        if type == "b":
            self.bp_num += 1
            return "b"+str(self.bp_num)
        self.tp_num += 1
        return "t"+str(self.tp_num)

    # only for primary keys for now
    def search_rid(self, base_rid, projected_columns_index, relative_version):
        # id of page corresponding to rid
        base_page_id = self.page_directory[base_rid][0]
        # offset value corresponding to rid
        base_record_offset = self.page_directory[base_rid][1]
        # actual page object which contains the rid
        base_page = self.buffer_pool.return_page(base_page_id)
        base_page.pin()
        # get indirection value of this base page
        indirect_rid = base_page.get_indirection(base_record_offset)
        # go to latest tail page, get its info
        tail_page_id = self.page_directory[indirect_rid][0]
        tail_record_offset = self.page_directory[indirect_rid][1]
        tail_page = self.buffer_pool.return_page(tail_page_id)
        tail_page.pin()
        for i in range(0, abs(relative_version)):
            if indirect_rid == base_rid:
                break
            # use indirection to go to last tail page
            indirect_rid = tail_page.get_indirection(tail_record_offset)
            tail_page_id = self.page_directory[indirect_rid][0]
            tail_record_offset = self.page_directory[indirect_rid][1]
            tail_page.unpin()
            tail_page = self.buffer_pool.return_page(tail_page_id)
            tail_page.pin()
        # continue until we have reached desired record version and have it in tail_location

        Schema = tail_page.get_schema(tail_record_offset)
        values = self.read_record(Schema, base_page.get_col_values(
            base_record_offset, projected_columns_index), tail_page.get_col_values(tail_record_offset, projected_columns_index))
        r = Record(indirect_rid, base_page.get_col_values(
            base_record_offset, [1] + [None for i in range(self.num_columns-1)])[0], values)
        tail_page.unpin()
        base_page.unpin()
        return r

    def read_record(self, schema, base_val, tail_val):
        values = []
        for i in range(0, len(schema)):
            if schema[i] == str(1):
                values.append(tail_val[i])
            else:
                values.append(base_val[i])
        return values

    def read(self, search_key, search_key_index, projected_columns_index, relative_version):
        base_rids = self.index.locate(search_key_index, search_key)[0]
        for i in base_rids:
            if not self.does_exist(i):
                base_rids.remove(i)
        if len(base_rids) == 0:
            return False
        records = []
        for rid in base_rids:
            records.append(self.search_rid(
                rid, projected_columns_index, relative_version))
        return records

    def sum(self, start_range, end_range, aggregate_column_index, relative_version):
        bp_rids = self.index.locate_range(start_range, end_range, 0)
        rid_list = []
        for rids in bp_rids:
            if rids != []:
                rid_list.append(*rids)
        bp_rids = rid_list
        print(bp_rids)
        for i in bp_rids:
            if not self.does_exist(i):
                bp_rids.remove(i)

        projected_col_index = [None]*self.num_columns
        projected_col_index[aggregate_column_index] = 1
        # Could increment records starting at 0
        records = []
        for rid in bp_rids:
            records.append(self.search_rid(rid, projected_col_index,
                           relative_version).columns[aggregate_column_index])
        return sum(records)

    def does_exist(self, rid):
        if rid in self.page_directory:
            return True
        return False

    def delete_rec(self, key):
        rid = self.index.locate(0, key)[0][0]
        if not self.does_exist(rid):
            return False
        rid_page_id = self.page_directory[rid][0]
        rid_record_offset = self.page_directory[rid][1]
        rid_page = self.buffer_pool.return_page(rid_page_id)
        rid_page.pin()
        rid_page.update_indirection(0, rid_record_offset)
        rid_page.unpin()
        self.page_directory.pop(rid)
        return True

    def __merge(self):
       # Variables that will need to be changed once other code is structured
        folder_path = ''
        page_id = 0
        with os.listdir(folder_path) as folder:
            for file in folder:  # loop to get all page groups written
                conslidated = PageGrp()  # New page group for consolidated records
                # get each record from file through offsets
                for offset in range(file.pages[0].num_records):
                    # get all values from record at offest
                    values = file.get_col_values(offset, [1]*len(file))
                    # Should actually be .select()
                    conslidated.pg_write(values)  # write to new page group
                    # add to page directory
                    self.page_directory[page_id] = conslidated
