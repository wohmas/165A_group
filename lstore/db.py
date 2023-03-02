from lstore.table import Table
import os


class Database():

    def __init__(self):
        self.tables = {}
        self.path = ""
        pass

    def open(self, path):
        cwd = os.getcwd()
        print(cwd)
        self.path = os.path.join(cwd, path)
        print(self.path)

        if os.path.exists(self.path):
            os.chdir(self.path)
            with open("database.txt", "r") as file:
                contents = file.read()
                key, value = contents.replace('{', '').replace('}', '').replace("'", '').split(':')
                print(key, value)
        else:
            os.mkdir(self.path)
            os.chdir(self.path)


    def close(self):
        print(self.tables)
        with open("database.txt", "w") as file:
            file.write(str(self.tables))
        pass

    """
    # Creates a new table
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def create_table(self, name, num_columns, key_index):
        # pass path
        table = Table(name, num_columns, key_index)

        # cwd = os.getcwd()
        # table_path = os.path.join(cwd, name)
        # if os.path.exists(table_path):
        #     print("Table already exists.")
        #     return self.get_table(name)
        # else:
        #     table = Table(name, num_columns, key_index)
        #     self.tables[name] = table
        #     os.mkdir(table_path)
        return table

    """
    # Deletes the specified table
    """

    def drop_table(self, name):
        pass

    """
    # Returns table with the passed name
    """

    def get_table(self, name):
        print(self.tables)
        return self.tables[name]
