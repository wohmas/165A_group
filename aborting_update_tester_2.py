from lstore.db import Database
from lstore.query import Query
from lstore.transaction import Transaction

db = Database()
db.open('aborting_delete_test')
test_table = db.get_table("test")

query = Query(test_table)

t = Transaction()

t.add_query(query.select, test_table, 1, 0, [1,1,1,1,1])
t.add_query(query.select, test_table, 5, 0, [1,1,1,1,1])
t.add_query(query.select, test_table, 2, 0, [1,1,1,1,1])

t.run()
result = query.select_version(5, 0, [1, 1, 1, 1, 1], -2)[0].columns
print(result)
db.close()