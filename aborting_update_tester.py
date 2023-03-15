from lstore.db import Database
from lstore.query import Query
from lstore.transaction import Transaction

db = Database()
db.open('aborting_delete_test')
test_table = db.create_table("test", 5, 0)

query = Query(test_table)

t = Transaction()
t.add_query(query.insert, test_table, *[1, 1, 1, 1, 1])
t.add_query(query.insert, test_table, *[2, 2, 2, 2, 2])
#t.add_query(query.update, test_table, 2, *[2, 4, 1, 1, 3])
t.add_query(query.insert, test_table, *[3, 3, 3, 3, 3])
t.add_query(query.insert, test_table, *[4, 4, 4, 4, 4])

t.run()

test_table.print_pg()

db.close()