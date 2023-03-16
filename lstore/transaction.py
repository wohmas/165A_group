from lstore.table import Table, Record
from lstore.index import Index
from lstore.query import Query


class Transaction:

    """
    # Creates a transaction object.
    """

    def __init__(self):
        self.queries = []
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
        self.getLocks()
        i = 1
        for query, args in self.queries:
            print("query: ", query.__name__)
            print(query.__name__ == "insert")
            result = query(*args)
            # If the query has failed the transaction should abort
            if result == False:
                print("Going to abort")
                return self.abort(i-1)
            i = i + 1
        return self.commit()

    def abort(self, num_queries):

        while(num_queries >= 1):
            #   if str(self.queries[num_queries][0]) == 'query.update':
            #       # self.queries[num_queries][1] is the table
            #       self.queries[num_queries][2][1] is the primary key
            #       self.queries[num_queries][1].undo_update(self.queries[num_queries][2][1])
            #
            print("trynig to enter the if statement")
            if self.queries[num_queries][0] == query.insert:
                self.queries[num_queries][1].delete(
                    self.queries[num_queries][2][0])
        #
        #   add the undo delete if condition
            num_queries = num_queries-1

        # TODO: do roll-back and any other necessary operations
        return False

    def commit(self):
        # TODO: commit to database
        return True
