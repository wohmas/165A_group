from lstore.db import Database
from lstore.query import Query

db = Database()
test_table = db.create_table('test', 5, 0)

query = Query(test_table)

# query.insert(6,5)
query.insert(917225897, 12, 213, 34, 0)
query.insert(12345, 213, 123, 45, 7)
query.insert(2, 213, 123, 45, 7)
query.insert(3, 213, 123, 45, 8)
query.insert(4, 213, 123, 45, 9)
query.insert(15, 213, 123, 45, 7)

query.update(2, *[None, None, 15, 3, None])
query.update(3, *[None, None, 15, 3, None])
query.update(2, *[None, 1, None, 4, None])
query.update(2, *[None, 1, None, 4, 30])
query.update(15, *[None, 1, None, 4, None])
query.update(15, *[None, None, None, None, None])
query.update(15, *[None, None, 68, 68, 68])

# query.table.print_pg()
# print(query.table.index.locate_range(2, 4, 0))
query.table.print_pg()
query.select_version(2, 0, [1, 1, 1, 1, 1], 0)[0].print_record()
print(query.delete(2))
print(query.select_version(2, 0, [1, 1, 1, 1, 1], -4))
print(query.sum_version(2, 4, 4, 0))
