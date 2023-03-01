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
        self.num_col = num_col
        self.isPinned = False
        self.rel_path = rel_path+"/pg_"+self.id+".txt"
        self.pages = self.read_from_file()

    def pg_write(self, values):
        self.isPinned = True
        self.isDirty = True
        for i in range(len(self.pages)):
            self.pages[i].write(values[i])
        self.isPinned = False

    def get_col_values(self, record_no, projected_columns_index):
        self.isPinned = True
        values = []
        for i in range(0, len(projected_columns_index)):
            if projected_columns_index[i] == 1:
                values.append(self.pages[i].get_int(record_no))
            else:
                values.append(None)
        self.isPinned = False
        return values

    def get_col_value(self, num, offset):
        return self.pages[num].get_int(offset)

    def write_to_file(self):
        self.isPinned = True
        with open(self.rel_path, "wb") as file:
            for page in self.pages:
                file.write(page.getAll())
        self.isPinned = False

    def read_from_file(self):
        self.isPinned = True
        page_list = []
        try:
            with open(self.rel_path, "rb") as file:
                byte = file.read(4096)
                while byte:
                    page_list.append(Page(byte))
            self.isPinned = False
        except:
            print("file does not exists")
            page_list = [Page() for i in range(self.num_col)]
        return page_list

    # so table does not directly interact with page objects
    def has_capacity(self):
        return self.pages[0].has_capacity(self)

    def num_records(self):
        return self.pages[0].num_records

    def get_indirection(self, offset):
        return self.pages[-1].get_int(offset)

    def update_indirection(self, value, offset):
        self.pages[-1].update_int(value, offset)

    def get_schema(self, offset):
        return self.pages[-2].get_int(offset)

    def update_schema(self, schema, offset):
        return self.pages[-2].update_int(schema, offset)


class BufferPool:
    def init(self, path, num_col):
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
        if self.files_in_mem >= 16:
            self.rem_page()

        # assuming buffer pool has space
        self.pages_in_mem[id] = PageGrp(id, self.path, self.num_col)
        self.files_in_mem += 1  # should max out at 16

    # table getter
    def return_page(self, id):
        if self.pages_in_mem.get(id) == None:
            self.add_page(self, id)

        return self.pages_in_mem.get(id)


class Table:

    """
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def __init__(self, name, num_columns, key):
        self.name = name
        self.nums = 0
        self.key = key
        self.num_columns = num_columns
        self.page_directory = {}
        self.page_num = 1
        self.latest_bp_id = 1
        self.latest_tp_id = 1
        self.index = Index(self)
        self.buffer_pool = BufferPool(name, num_columns)
        pass

    # now irrelevant because pgroup handles this?
    def pg_write(self, pg, values):
        for i in range(len(pg)):
            pg[i].write(values[i])

    # locations will now just be base/page id, along with offset etc.
    def addpd(self, rid, locations):
        self.page_directory[rid] = locations

    def update(self, key, cols):
        # ask bufferpool for latest tail page
        tail_page = self.buffer_pool.return_page(self.latest_tp_id)
        # if full, create new tail page ID
        # by requesting the page bufferpool (should) automatically create it
        if tail_page.has_capacity() == False:
            self.page_num += 1
            self.latest_tp_id = self.page_num
            tail_page = self.buffer_pool.return_page(self.latest_tp_id)

        tp_rid = self.create_rid()
        # use index to get base rid related to key
        # find basepage ID from page directory
        bp_rid = self.index.locate(0, key)
        # find basepage ID from page directory
        bp_id = self.page_directory[bp_rid[0]][0]
        base_offset = self.page_directory[bp_rid[0]][1]
        # get basepage from bufferpool using ID
        base_page = self.buffer_pool.return_page(bp_id)
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
            if(last_schema[i] == '1' and cols[i] == None):
                new_schema = new_schema[:i] + "1" + new_schema[i+1:]
                val[i] = last_update_record.get_col_values(
                    self, i, last_update_record_offset)
        # ..go from there
        base_page.update_schema(new_schema, base_offset)
        # hopefully this works
        tail_page.pg_write([*val, new_schema, indirection])
        locations = [self.latest_tp_id, tail_page.num_records() - 1]
        self.addpd(tp_rid, locations)

    # STILL NOT UPDATED FOR BUFFERPOOL

    def print_pg(self):
        '''For Internal use: prints all RIDs and their values found in page directory'''
        for i in self.page_directory.keys():
            print("rid : ", i)
            for j in range(0, len(self.page_directory[i][0])-2):
                print(f"col {j}: ", self.page_directory[i][0][j].get_int(
                    self.page_directory[i][1]))
            print(
                "schema : ", self.page_directory[i][0][-2].get_str(self.page_directory[i][1]))
            print("indirection : ",
                  self.page_directory[i][0][-1].get_int(self.page_directory[i][1]))
            print("======================================================")

    def insert(self, values, schema):
        # ask bufferpool for newest base page
        # call has_capacity on page_group
        base_page = self.buffer_pool.return_page(self.latest_bp_id)
        # if full, create new base page ID
        # by requesting the page bufferpool (should) automatically create it
        if base_page.has_capacity() == False:
            self.page_num += 1
            self.latest_bp_id = self.page_num
            base_page = self.buffer_pool.return_page(self.latest_bp_id)

        rid = self.create_rid()
        # write values to base page
        base_page.pg_write([*values, schema, rid])
        # update page directory and index
        locations = [self.latest_bp_id, base_page.num_records() - 1]
        self.addpd(rid, locations)
        self.index.insert(rid, values[0])

        return True

    def create_rid(self):
        self.nums += 1
        return self.nums

    # only for primary keys for now
    def search_rid(self, base_rid, projected_columns_index, relative_version):

        # id of page corresponding to rid
        base_page_id = self.page_directory[base_rid][0]
        # offset value corresponding to rid
        base_record_offset = self.page_directory[base_rid][1]
        # actual page object which contains the rid
        base_page = self.buffer_pool.return_page(base_page_id)
        # get indirection value of this base page
        indirect_rid = base_page.get_indirection(base_record_offset)

        # go to latest tail page, get its info
        tail_page_id = self.page_directory[indirect_rid][0]
        tail_record_offset = self.page_directory[indirect_rid][1]
        tail_page = self.buffer_pool.return_page(tail_page_id)

        for i in range(0, abs(relative_version)):
            if indirect_rid == base_rid:
                break
            # use indirection to go to last tail page
            indirect_rid = tail_page.get_indirection(tail_record_offset)
            tail_page_id = self.page_directory[indirect_rid][0]
            tail_record_offset = self.page_directory[indirect_rid][1]
            tail_page = self.buffer_pool.return_page(tail_page_id)
            # continue until we have reached desired record version and have it in tail_location

        Schema = tail_page.get_schema(tail_record_offset)
        values = self.read_record(projected_columns_index, Schema,
                                  tail_page, base_page, tail_record_offset, base_record_offset)

        r = Record(indirect_rid, base_page.get_col_value(
            self, 0, base_record_offset), values)
        ret = []
        ret.append(r)
        return ret

    def read_record(self, projected_columns_index, Schema, tail_page, base_page, tail_record_offset, base_record_offset):
        values = []
        for i in range(0, len(projected_columns_index)):
            if projected_columns_index[i] == 1:
                if Schema[i] == str(1):
                    values.append(tail_page.get_col_value(
                        self, i, tail_record_offset))
                else:
                    values.append(base_page.get_col_value(
                        self, i, base_record_offset))
            else:
                # assuming we don't want to just leave it empty
                values.append(None)
        return values

    def read(self, search_key, search_key_index, projected_columns_index, relative_version):
        base_rid = self.index.locate(search_key_index, search_key)[0]
        if not self.does_exist(base_rid):
            return False
        return self.search_rid(base_rid, projected_columns_index, relative_version)

    def sum(self, start_range, end_range, aggregate_column_index, relative_version):
        bp_rids = self.index.locate_range(start_range, end_range, 0)
        for i in bp_rids:
            if not self.does_exist(i):
                bp_rids.remove(i)

        projected_col_index = [0]*self.num_columns
        projected_col_index[aggregate_column_index] = 1
        # Could increment records starting at 0
        records = []
        for rid in bp_rids:
            records.append(self.search_rid(rid, projected_col_index, relative_version)[
                           0].columns[aggregate_column_index])
        return sum(records)

    def does_exist(self, rid):
        if rid in self.page_directory:
            return True
        return False

    def delete_rec(self, key):
        rid = self.index.locate(0, key)[0]
        if not self.does_exist(rid):
            return False
        rid_page_id = self.page_directory[rid][0]
        indirect_rid = rid_page_id.get_indirection(self.page_directory[rid][1])
        rid_record_offset = self.page_directory[indirect_rid][1]
        rid_page = self.buffer_pool.return_page(rid_page_id)
        rid_page.update_indirection(0, rid_record_offset)

        self.page_directory.pop(rid)

        return True

    def __merge(self):
        print("merge is happening")
        pass
