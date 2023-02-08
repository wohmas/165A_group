from lstore.db import Database
from lstore.query import Query


db = Database()
grades_table = db.create_table('test', 2, 0)
query = Query(grades_table)

query.insert(5,6)

