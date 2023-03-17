from lstore.table import Table, Record
from lstore.index import Index
from lstore.query import Query


class Transaction:

    """
    # Creates a transaction object.
    """

    def __init__(self):
        self.queries = []
        self.delete_data = []
        self.table_map = {}
        self.tables = []

    """
    # Adds the given query to this transaction
    # Example:
    # q = Query(grades_table)
    # t = Transaction()
    # t.add_query(q.update, grades_table, 0, *[None, 1, None, 2, None])
    """

    def add_query(self, query, table, *args):

        self.queries.append((query, args))
        if table not in self.tables:
            self.tables.append(table)
        self.table_map[query] = table

        # use grades_table for aborting

    def getLocks(self):
        gotLock = True
        for query, args in self.queries:
            func_name = query.__name__
            if func_name == "insert":
                pass
            elif func_name == "update":
                gotLock = self.table_map[query].get_update_locks(
                    transaction=self, primary_key=args[0])
            elif func_name == "delete":
                gotLock = self.table_map[query].get_del_lock(
                    primary_key=args[0], transaction=self)
            elif func_name == "sum":
                gotLock = self.table_map[query].get_read_locks(
                    start_range=args[0], end_range=args[1], relative_version=0, transaction=self)
            elif func_name == "sum_version":
                gotLock = self.table_map[query].get_read_locks(
                    start_range=args[0], end_range=args[1], relative_version=args[3], transaction=self)
            elif func_name == "select":
                gotLock = self.table_map[query].get_read_locks(
                    search_key=args[0], search_key_index=args[1], relative_version=0, transaction=self)
            elif func_name == "select_version":
                gotLock = self.table_map[query].get_read_locks(
                    search_key=args[0], search_key_index=args[1], relative_version=args[3], transaction=self)
            if gotLock == False:
                self.releaseLocks()
                return False
        return True

    def releaseLocks(self):
        for table in self.tables:
            table.lock_manager.releaseAllLocks(self)
    # If you choose to implement this differently this method must still return True if transaction commits or False on abort

    def run(self):
        while True:
            if self.getLocks():
                break
        
        i = 0

        for query, args in self.queries:
            # checking for delete
            if query.__name__ == "delete":
                # print("delete query")
                self.delete_data.append(
                    self.table_map[query].return_delete_data(*args))
            result = None
            if query.__name__ == "insert" or query.__name__ == "update":

                result = query(*args, transaction=self)
            else:
                result = query(*args)

            # If the query has failed the transaction should abort
            # print("result", result)
            if result == False:
                #print("Going to abort")
                return self.abort(i-1)
            i = i + 1
        # RELEASING LOCKS??
        return self.commit()

    def abort(self, num_queries):

        while(num_queries >= 0):
            #   checking for update
            query = self.queries[num_queries][0]
            func_name = self.queries[num_queries][0].__name__
            if func_name == "update":
                self.table_map[query].undo_update(
                    self.queries[num_queries][1][0])

        #    check for insert
            # print("checking for insert")
            if func_name == "insert":
                self.table_map[query].delete_rec(
                    self.queries[num_queries][1][0])

        #   check for delete
            # print("checking for delete")
            if func_name == "delete":
                # print("undoing delete")
                delete_list = self.delete_data.pop()
                self.table_map[query].undo_delete(
                    delete_list[0], delete_list[1], delete_list[2])
                # do delete stuff

            num_queries = num_queries-1
        self.releaseLocks()

        return False

    def commit(self):
        # TODO: commit to database
        self.releaseLocks()
        return True
