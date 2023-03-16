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
        pass

    """
    # Adds the given query to this transaction
    # Example:
    # q = Query(grades_table)
    # t = Transaction()
    # t.add_query(q.update, grades_table, 0, *[None, 1, None, 2, None])
    """

    def add_query(self, query, table, *args):
        self.queries.append((query, table, args))
        # use grades_table for aborting

    def getLocks(self):
        pass

    # If you choose to implement this differently this method must still return True if transaction commits or False on abort
    def run(self):
        self.getLocks()
        i = 1
        for query, table, args in self.queries:
            # checking for delete
            if len(self.queries[i-1][2]) == 1:
                print("delete query")
                print(args)
                self.delete_data.append(self.queries[i-1][1].return_delete_data(*args))
            result = query(*args)
            # If the query has failed the transaction should abort
            print("Query Result:")
            print(result)
            if result == False:
                print("Going to abort")
                print(self.queries[i-1][1].print_pg())
                return self.abort(i-1)
            i = i + 1
        #RELEASING LOCKS??    
        return self.commit()

    def abort(self, num_queries):

        while(num_queries >= 1):
        #   checking for update

            if len(self.queries[num_queries][2]) == self.queries[num_queries][1].num_columns + 1:
         #       print(self.queries[num_queries][1])
          #      print(self.queries[num_queries][2][1])
                 self.queries[num_queries][1].undo_update(self.queries[num_queries][2][0])
        
        #    check for insert
            print("checking for insert")
            print(len(self.queries[num_queries][2]))
            if len(self.queries[num_queries][2]) == self.queries[num_queries][1].num_columns:
                self.queries[num_queries][1].delete_rec(self.queries[num_queries][2][0])
               
        #   check for delete
            print("checking for delete")
            print(len(self.queries[num_queries][2]))
            if len(self.queries[num_queries][2]) == 1:
                print("undoing delete")
                delete_list = self.delete_data.pop()
                self.queries[num_queries][1].undo_delete(delete_list[0], delete_list[1], delete_list[2])
                print(self.queries[num_queries][1].page_directory)
                #do delete stuff

            num_queries = num_queries-1   

        # TODO: do roll-back and any other necessary operations
        return False

    def commit(self):
        # TODO: commit to database
        return True
