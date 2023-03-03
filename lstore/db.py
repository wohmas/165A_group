from lstore.table import Table
import os
import json


class Database():

    def __init__(self):
        self.tables = {}
        self.table_names = []
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
                self.table_names = json.loads(file.read())
                print(self.table_names)
                #contents = file.read()
                #key, value = contents.replace('{', '').replace('}', '').replace("'", '').split(':')
                #print(key, value)
        else:
            os.mkdir(self.path)
            os.chdir(self.path)

    def close(self):
        print(self.tables)
        # write database metadata to file (table names)
        with open("database.txt", "w") as file:
            file.write(json.dumps(self.table_names))
            print(json.dumps(self.table_names))

        # write table metadata to file (all table attributes)
        for table in self.tables.values():
            table_attributes = []
            table_attributes.append(table.name)
            table_attributes.append(table.key)
            table_attributes.append(table.num_columns)
            table_attributes.append(table.page_directory)
            table_attributes.append(table.nums)
            table_attributes.append(table.page_num)
            table_attributes.append(table.page_range_map)
            table_attributes.append(table.bp_num)
            table_attributes.append(table.tp_num)
            print(table_attributes)
            with open(table.name+".txt", "w") as file:
                file.write(table_attributes)

        pass

    """
    # Creates a new table
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def create_table(self, name, num_columns, key_index):
        # pass path

        cwd = os.getcwd()
        table = Table(name, num_columns, key_index)

        table_path = os.path.join(cwd, name)
        if os.path.exists(table_path):
            print("Table already exists.")
            return self.get_table(name)
        else:
            self.tables[name] = table
            self.table_names.append(name)
            os.mkdir(table_path)
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
