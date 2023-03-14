from lstore.db import Database
from lstore.query import Query

db = Database()
db.open('aborting_delete_test')
test_table = db.create_table("test", 5, 0)

query = Query(test_table)


query.insert(2, 213, 123, 45, 7)

query.table.print_pg()

query.delete(2)




db.close()