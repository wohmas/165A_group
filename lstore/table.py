from lstore.index import Index
from time import time
from lstore.page import Page
from lstore.lock_manager import Lock_Manager
from lstore.lock_manager import TPLock


import os
import threading
import math
import copy

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
        self.dir = rel_path
        self.rel_path = f'./{rel_path}/{self.id}.txt'
        self.pages = self.read_from_file()
        self.tps = 0

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

    def get_col_value(self, col, offset):
        return self.pages[col].get_int(offset)

    def write_to_file(self):
        with open(self.rel_path, "wb") as file:
            rec_num = self.pages[0].num_records.to_bytes(8, "little")
            file.write(rec_num)
            tps = self.tps.to_bytes(8, "little")
            file.write(tps)
            for page in self.pages:
                file.write(page.getAll())

    def read_from_file(self):
        page_list = []
        try:
            with open(self.rel_path, "rb") as file:
                rec_num = file.read(8)
                r = int.from_bytes(rec_num, "little")
                tps = file.read(8)
                self.tps = int.from_bytes(tps, "little")
                while True:
                    bytes = file.read(4096)
                    if not bytes:
                        break
                    page_list.append(Page(r, bytes))

        except:
            # print("file does not exists")
            page_list = [Page(0, -1) for i in range(self.num_col + 4)]
        return page_list

    def print_contents(self, offset):
        vals = self.get_col_values(offset, [1 for i in range(self.num_col)])
        print(f"columns : {vals}")
        print(f"rid: {self.get_bp_rid(offset)}")
        print(f"schema: {self.get_schema(offset)}")
        print(f"indirection: {self.get_indirection(offset)}")

    def get_rid(self, offset):
        return self.pages[-4].get_int(offset)

    # so table does not directly interact with page objects
    def get_bp_rid(self, offset):
        return self.pages[-3].get_int(offset)

    def has_capacity(self):
        return self.pages[0].has_capacity()

    def num_records(self):
        return self.pages[0].num_records

    def get_indirection(self, offset):
        return self.pages[-1].get_int(offset)

    def update_indirection(self, value, offset):
        self.isDirty = True
        self.pages[-1].update_int(value, offset)

    def get_schema(self, offset):
        return self.pages[-2].get_str(offset)

    def update_schema(self, schema, offset):
        self.isDirty = True
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
        self.lock = threading.Lock()

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
        self.lock.acquire()
        if self.pages_in_mem.get(id) == None:
            self.add_page(id)
        self.lock.release()

        return self.pages_in_mem.get(id)

    def flush(self):
        for id in self.pages_in_mem.keys():
            if self.pages_in_mem[id].isDirty == True:
                self.pages_in_mem[id].write_to_file()


class Table:

    """
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def __init__(self, name, num_columns, key,
                 page_directory={}, nums=0, tids=2**64, page_num=0, page_range_map={}, bp_num=0, tp_num=0, merge_count=0):
        # recieve database path, create tail page path by appending name to it
        self.rid_lock = threading.Lock()
        self.tid_lock = threading.Lock()
        self.pid_lock = threading.Lock()
        self.name = name
        self.key = key
        self.num_columns = num_columns
        self.page_directory = page_directory
        self.rids = nums
        self.tids = tids

        self.page_num = page_num
        self.page_range_map = page_range_map
        self.bp_num = bp_num
        self.tp_num = tp_num
        self.latest_bp_id = self.create_pid("b")
        self.buffer_pool = BufferPool(name, num_columns)
        self.index = Index(self)
        self.merge_count = merge_count
        self.merge_group = 0
        self.update_count = 0
        self.rid_lock_map = {}
        self.lock_manager = Lock_Manager()

    def flush_bp(self):
        self.buffer_pool.flush()

    def get_tail_pg(self, bp_id):
        bp_id = int(bp_id.split("_")[1])
        grp = math.ceil(bp_id/10)

        if grp not in self.page_range_map.keys():
            self.pid_lock.acquire()
            self.page_range_map[grp] = self.create_pid("t")
            self.pid_lock.release()
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
        # print("tp_id: ", tp_id)
        # print("================================")
        return tail_page

    def pg_write(self, pg, values):
        for i in range(len(pg)):
            pg[i].write(values[i])

    # locations will now just be base/page id, along with offset etc.
    def addpd(self, rid, locations):
        self.page_directory[rid] = locations

    def update(self, key, cols):
        # if self.index.locate(0, key) != []:
        #     return
        # use index to get base rid related to key
        # find basepage ID from page directory

        bp_rid = self.index.locate(0, key)[0]
        print("bp_rid: ", bp_rid)

        # find basepage ID from page directory
        bp_id = self.page_directory[bp_rid][0]
        base_offset = self.page_directory[bp_rid][1]
        # get basepage from bufferpool using ID
        base_page = self.buffer_pool.return_page(bp_id)
        base_page.pin()

        # generate schema for updated columns
        if cols[0] != None:
            if self.index.locate(0, cols[0]) != []:
                print("same primary key")
                return
        new_schema = ''.join('0' if val is None else '1' for val in cols)
        for i in range(0, len(new_schema)):
            if new_schema[i] == '1':

                val = self.index.get_latest_val(base_page, base_offset, i)
                self.index.remove(i, bp_rid, val)
                self.index.insert(bp_rid, cols[i], i)

        # ask bufferpool for latest tail page
        tail_page = self.get_tail_pg(bp_id)
        tail_page.pin()
        # self.check_tps(tail_page)
        # if full, create new tail page ID
        # by requesting the page bufferpool (should) automatically create it
        self.tid_lock.acquire()
        tp_rid = self.create_tid()
        self.tid_lock.release()
        # get rid from base indirection column via pagegroup
        indirection = base_page.get_indirection(base_offset)
        # update indirection value of base record via pagegroup

        # get schema from base record via pagegroup
        base_page.update_indirection(tp_rid, base_offset)

        last_schema = base_page.get_schema(base_offset)
        # Make input cols mutable
        val = list(cols)
        # use old indirection value (first step of this block) to get corresponding page directory ID
        last_update_record_id = self.page_directory[indirection][0]
        last_update_record_offset = self.page_directory[indirection][1]
        # use bufferpool to get corresponding pagegroup object
        last_update_record = self.buffer_pool.return_page(
            last_update_record_id)
        last_update_record.pin()
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
        tail_page.pg_write([*val, tp_rid, bp_rid, new_schema, indirection])
        locations = [tail_page.get_id(), tail_page.num_records() - 1]
        tail_page.unpin()
        base_page.unpin()
        last_update_record.unpin()
        self.addpd(tp_rid, locations)

        # self.update_count += 1
        # if self.update_count >= 512:
        #     self.update_count = 0
        #     self.init_merge()

    def print_pg(self):
        '''For Internal use: prints all RIDs and their values found in page directory'''
        for i in self.page_directory.keys():
            print("rid : ", i)
            pg = self.buffer_pool.return_page(self.page_directory[i][0])
            pg.print_contents(self.page_directory[i][1])
            print("======================================================")

    def insert(self, values, schema):
        if self.index.locate(0, values[0]) != []:
            return
        # ask bufferpool for newest base page
        # call has_capacity on page_group
        # print("Current bp_num:" + str(self.bp_num))
        base_page = self.buffer_pool.return_page(self.latest_bp_id)
        base_page.pin()
        # if full, create new base page ID
        # by requesting the page bufferpool (should) automatically create it
        if base_page.has_capacity() == False:
            # print("in has cap false")
            self.pid_lock.acquire()
            self.latest_bp_id = self.create_pid("b")
            self.pid_lock.release()
            # print(self.latest_bp_id)
            base_page.unpin()
            base_page = self.buffer_pool.return_page(self.latest_bp_id)
            base_page.pin()
        self.rid_lock.acquire()
        rid = self.create_rid()
        self.rid_lock.release()
        # write values to base page
        base_page.pg_write([*values, rid, rid, schema, rid])
        # update page directory and index
        locations = [base_page.get_id(), base_page.num_records() - 1]
        base_page.unpin()
        self.index.insert_all_existing_index(rid, values)
        self.addpd(rid, locations)
        return True

    def create_rid(self):
        self.rids += 1
        self.rid_lock_map[self.rids] = TPLock()
        return self.rids

    def create_tid(self):
        self.tids -= 1
        self.rid_lock_map[self.tids] = TPLock()
        return self.tids

    def create_pid(self, type):
        if type == "b":
            self.bp_num += 1
            return "b_"+str(self.bp_num)
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
        # self.check_tps(tail_page)
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
        r = Record(base_rid, values[0], values)
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
        base_rids = self.index.locate(search_key_index, search_key)
        for i in base_rids:
            if not self.does_exist(i):
                base_rids.remove(i)

        # if len(base_rids) == 0:
        #    return False
        records = []
        for rid in base_rids:
            records.append(self.search_rid(
                rid, projected_columns_index, relative_version))
        return records

    def sum(self, start_range, end_range, aggregate_column_index, relative_version):
        bp_rids = self.index.locate_range(start_range, end_range, 0)

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

    def get_read_locks(self, relative_version, transaction,  search_key=-1, search_key_index=-1, start_range=-1, end_range=-1):
        base_rids = None
        if search_key_index == -1:
            base_rids = self.index.locate_range(start_range, end_range, 0)
        else:
            base_rids = self.index.locate(search_key_index, search_key)

        for i in base_rids:
            if not self.does_exist(i):
                base_rids.remove(i)
        for base_rid in base_rids:
            self.lock_manager.getLock(
                transaction, self.rid_lock_map[base_rid], "s")
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
            # self.check_tps(tail_page)
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
            tail_page.unpin()
            if indirect_rid != base_rid:
                self.lock_manager.getLock(
                    transaction, self.rid_lock_map[indirect_rid], "s")
        return True

    def does_exist(self, rid):
        if rid in self.page_directory:
            return True
        return False

    def delete_rec(self, key):
        rid = self.index.locate(0, key)[0]
        if not self.does_exist(rid):
            return False
        rid_page_id = self.page_directory[rid][0]
        rid_record_offset = self.page_directory[rid][1]
        rid_page = self.buffer_pool.return_page(rid_page_id)
        rid_page.pin()
        rid_page.update_indirection(0, rid_record_offset)
        rid_page.unpin()
        self.index.remove(0, rid, key)
        print(self.page_directory)
        self.page_directory.pop(rid)
        return True

    def undo_delete(self, rid, page_id, offset, indirection):
        #   get the page
        #
        base_page = self.buffer_pool.return_page(page_id)
        base_page.pin()

        # fix indirection
        base_page.update_indirection(indirection, offset)
    #
    #   add back to page directory
        locations = [page_id, offset]
        self.addpd(rid, locations)
#
        # print(self.page_directory)
        # print(base_page.get_col_value(0, offset))
    #   add back to index
        self.index.insert(rid, base_page.get_col_value(0, offset), 0)

        print(self.index)
    #
    #
    #

    # for undoing update
    # will delete latest tail record and make neccessary adjustments

    def undo_update(self, primary_key):
        base_rid = self.index.locate(0, primary_key)

        base_page_id = self.page_directory[base_rid[0]][0]
        # offset value corresponding to rid
        base_record_offset = self.page_directory[base_rid[0]][1]
        # actual page object which contains the rid
        base_page = self.buffer_pool.return_page(base_page_id)
        base_page.pin()
        # get indirection value of this base page
        # latest_rid is to save for removing from page directory at the end,
        # indirect_rid is for the for loop
        latest_rid = base_page.get_indirection(base_record_offset)
        indirect_rid = base_page.get_indirection(base_record_offset)
        # go to latest tail page, get its info
        print(indirect_rid)
        print(self.page_directory)
        tail_page_id = self.page_directory[indirect_rid][0]
        tail_record_offset = self.page_directory[indirect_rid][1]
        tail_page = self.buffer_pool.return_page(tail_page_id)
        tail_page.pin()
        self.check_tps(tail_page)

        # we want second to last tail record every time so relative version is always -1
        for i in range(0, abs(-1)):
            if indirect_rid == base_rid:
                break
            # use indirection to go to last tail page
            indirect_rid = tail_page.get_indirection(tail_record_offset)
            tail_page_id = self.page_directory[indirect_rid][0]
            tail_record_offset = self.page_directory[indirect_rid][1]
            tail_page.unpin()
            tail_page = self.buffer_pool.return_page(tail_page_id)
            tail_page.pin()

        # update indirection of base page
        base_page.update_indirection(indirect_rid, base_record_offset)

        # update schema of base page
        base_page.update_schema(tail_page.get_schema(
            tail_record_offset), base_record_offset)

        # "delete" record
        self.page_directory.pop(latest_rid)
        base_page.unpin()
        tail_page.unpin()

    # Helper functions to be used with merge

    def merge_latest_val(self, pg, offset, column_number):
        if pg.get_schema(offset)[column_number] == '0':
            ret = pg.get_col_value(column_number, offset)
            return ret

        indirection = pg.get_indirection(offset)
        tail_page_id = self.page_directory[indirection][0]
        tail_record_offset = self.page_directory[indirection][1]
        tail_page = None
        if tail_page_id in self.buffer_pool.pages_in_mem.keys():
            tail_page = self.buffer_pool.pages_in_mem[tail_page_id]
        else:
            tail_page = PageGrp(tail_page_id, self.name, self.num_columns)
        val = tail_page.get_col_value(column_number, tail_record_offset)
        return val

    def check_tps(self, tail_page):
        count = tail_page.num_records()-1
        tid = tail_page.get_rid(count)
        while tid < tail_page.tps:
            base_rid = tail_page.get_bp_rid(count)
            base_offset = self.page_directory[base_rid][1]
            base_page = self.buffer_pool.return_page(
                self.page_directory[base_rid][0])
            base_page.pin()
            if base_page.get_indirection(base_offset) == base_rid:
                base_page.unpin()
                count -= 1
                tid = tail_page.get_rid(count)
                continue
            schema = tail_page.get_schema(count)
            indirection = tail_page.get_indirection(count)
            base_page.update_schema(schema, base_offset)
            base_page.update_indirection(tid)
            base_page.unpin()
            count -= 1
            tid = tail_page.get_rid(count)

    def get_bp_copies(self, page_group):
        start = (page_group - 1)*10 + 1
        copies = []
        for i in range(start, min(start+10, self.bp_num+1)):
            bp = None
            id = "b_"+str(i)
            if id in self.buffer_pool.pages_in_mem.keys():
                bp = copy.deepcopy(self.buffer_pool.pages_in_mem[id])
            else:
                bp = copy.deepcopy(PageGrp(id, self.name, self.num_columns))
            bp.id = "bm"+str(self.merge_count)+"_"+str(i)
            bp.rel_path = f'./{self.name}/{bp.id}.txt'

            copies.append(bp)
        return copies

    '''We were unable to get merge to function without throwing errors with the 
       file writing system. Below is the skeleton code that we worked on that
       holds the idea of how we tried to implement it. To be working by next milestone.'''

    def merge(self):
        self.merge_count += 1
        self.merge_group += 1
        if self.merge_group > len(self.page_range_map):
            self.merge_group = 1
        new_basepages = self.get_bp_copies(self.merge_group)
        tps = 2**64-1
        update_dict = {}
        for page in new_basepages:
            for i in range(page.num_records()):
                rid = page.get_bp_rid(i)
                for j in range(self.num_columns):
                    value = self.merge_latest_val(page, i, j)
                    page.pages[j].update_int(value, i)
                page.update_schema('0' * self.num_columns, i)
                page.update_indirection(rid, i)
                tid = page.get_indirection(i)
                if tid < tps:
                    tps = tid
                update_dict[rid] = [page.id, i]
        for page in new_basepages:
            page.tps = tps
            page.write_to_file()

        for rid in update_dict.keys():
            self.page_directory.update({rid: update_dict[rid]})

    def init_merge(self):

        # self.update_count = 0
        print("in init merge")
        merge_thread = threading.Thread(target=self.merge, name="merger")
        merge_thread.start()
