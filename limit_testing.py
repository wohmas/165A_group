from lstore.db import Database
from lstore.query import Query


db = Database()
grades_table = db.create_table('test', 4, 0)
query = Query(grades_table)

for i in range(7):
    query.insert(5, 6, 8, 1)

print(query.table.page_directory)
