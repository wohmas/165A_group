from lstore.db import Database
from lstore.query import Query

db = Database()
db.open('aborting_update_test')
test_table = db.create_table("test", 5, 0)

query = Query(test_table)


query.insert(2, 213, 123, 45, 7)

query.update(2, *[None, 1, None, 4, None])
query.update(2, *[None, 1, None, 4, 30])

query.table.print_pg()

query.table.delete_latest(2)
print("Only two records w/ primary key 2 left ")
query.table.print_pg()
query.table.delete_latest(2)
print("Only one record w/ primary key 2 left ")
query.table.print_pg()

db.close()