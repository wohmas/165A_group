from lstore.db import Database
from lstore.query import Query

db = Database()
test_table = db.create_table('test', 2, 0)

query = Query(test_table)

query.insert(5,6)
query.insert(5,6)

print(query.table.bp[0].num_records)