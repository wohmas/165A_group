from lstore.db import Database
from lstore.query import Query

db = Database()
test_table = db.create_table('test', 5, 0)

query = Query(test_table)

# query.insert(6,5)
query.insert(917225897, 12, 213, 34, 0)
query.insert(12345, 213, 123, 45, 7)
query.insert(12345, 213, 123, 45, 7)
query.insert(12345, 213, 123, 45, 7)
query.insert(12345, 213, 123, 45, 7)
query.insert(12345, 213, 123, 45, 7)

list(query.table.index.indices[0].values())
