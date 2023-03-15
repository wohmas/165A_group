from lstore.db import Database
from lstore.query import Query
from lstore.transaction import Transaction

db = Database()
db.open('aborting_delete_test')
test_table = db.create_table("test", 5, 0)

query = Query(test_table)

query.insert(1, 1, 1, 1, 1)
test_table.print_pg()
query.delete(1)
test_table.undo_delete(1, "b_1", 0, 1)
query.update(1, *[None, 2, 2, 2, 2])

print("pg directory after updaye: ", test_table.page_directory)
test_table.print_pg()

db.close()
