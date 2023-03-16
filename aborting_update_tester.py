from lstore.db import Database
from lstore.query import Query
from lstore.transaction import Transaction

db = Database()
db.open('aborting_delete_test')
test_table = db.create_table("test", 5, 0)

query = Query(test_table)

t = Transaction()
t2 = Transaction()
t.add_query(query.insert, test_table, *[1, 1, 1, 1, 1])
t2.add_query(query.update, test_table, 1, *[1, 1, 1, 1, 1])
t.add_query(query.insert, test_table, *[1, 1, 1, 1, 1])
t.add_query(query.insert, test_table, *[1, 1, 1, 1, 1])
t.add_query(query.insert, test_table, *[1, 1, 1, 1, 1])
t.add_query(query.insert, test_table, *[1, 1, 1, 1, 1])
t.add_query(query.insert, test_table, *[2, 2, 2, 2, 2])
t.add_query(query.insert, test_table, *[3, 3, 3, 3, 3]) 
t.add_query(query.insert, test_table, *[4, 4, 4, 4, 4])
t2.add_query(query.update, test_table, 3, *[None, 3, 2, 1, 0])
t2.add_query(query.update, test_table, 2, *[None, 2, 1, 1, 4])
t2.add_query(query.select, test_table, 2, 0, [1, 1, 1, 1, 1])
t2.add_query(query.select_version, test_table, 2, 0, [1, 1, 1, 1, 1], 0)
t2.add_query(query.sum, test_table, 0, 1, 0)
t2.add_query(query.sum_version, test_table, 0, 1, 0, 0)
t2.add_query(query.delete, test_table, 4)
t.add_query(query.insert, test_table, *[5, 5, 5, 5, 5])
t.add_query(query.insert, test_table, *[5, 5, 5, 5, 5])
t.add_query(query.insert, test_table, *[6, 6, 6, 6, 6])





t.run()
t2.run()
test_table.print_pg()

db.close()