from lstore.db import Database
from lstore.query import Query

db = Database()
db.open('./ECS165')
test_table = db.create_table("test", 5, 1)
#test2_table = db.create_table("test2", 5, 1)

query = Query(test_table)
#query2 = Query(test2_table)

# query.insert(6,5)
query.insert(91, 12, 213, 34, 0)
query.insert(12, 213, 123, 45, 7)
query.insert(2, 213, 123, 45, 7)
query.insert(3, 213, 123, 45, 8)

query.insert(4, 213, 123, 45, 9)
query.insert(15, 213, 123, 45, 7)
query.insert(16, 213, 123, 45, 7)
query.insert(17, 213, 123, 45, 7)

query.insert(18, 213, 123, 45, 7)
query.insert(19, 213, 123, 45, 7)
query.insert(20, 56, 4, 45, 7)
# query.insert(12, 1, 1, 1, 1)

# query.table.index.create_index(4)
query.update(12, *[200, None, None, None, None])
query.update(20, *[12, None, None, None, None])
query.update(2, *[None, None, 15, 3, None])
query.update(3, *[None, None, 15, 3, None])
query.update(15, *[None, 1, None, 4, None])
# query.table.merge()
query.update(12, *[None, None, 68, 68, 68])
query.update(2, *[None, 1, None, 4, None])
query.update(2, *[None, 1, None, 4, 30])
query.update(15, *[None, None, None, None, None])
query.update(15, *[None, None, 68, 68, 68])

# query.table.print_pg()
# print(query.table.index.locate_range(2, 4, 0))

print("page_range:\n", query.table.page_range_map)
print()
query.table.print_pg()

r = query.select_version(7, 4, [1, 1, 1, 1, 1], 0)
for i in r:
    i.print_record()
# print(query.delete(2))
# print(query.select_version(2, 0, [1, 1, 1, 1, 1], -4))
print(query.sum_version(2, 10, 4, 0))
# db.close()
