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
        self.path = os.path.join(cwd, path)

        if os.path.exists(self.path):
            os.chdir(self.path)
            with open("database.txt", "r") as file:
                self.table_names = json.loads(file.read())
            for i in range(0, len(self.table_names)):
                with open(self.table_names[i]+".txt", "r") as file:
                    table_attributes = []
                    table_attributes = json.loads(file.read())
                    #########
                    name = self.table_names[i]
                    pg_dir = {}
                    for key in table_attributes[3].keys():
                        pg_dir[int(key)] = table_attributes[3][key]
                    # print("PAGE DIR: ", pg_dir)

                    pg_range = {}
                    for key in table_attributes[7].keys():
                        pg_range[int(key)] = table_attributes[7][key]

                    # print("pg directory:\n", table_attributes[3])
                    name = Table(name=table_attributes[0], num_columns=table_attributes[1], key=table_attributes[2],
                                 page_directory=pg_dir, nums=table_attributes[
                                     4], tids=table_attributes[5], page_num=table_attributes[6],
                                 page_range_map=pg_range, bp_num=table_attributes[8], tp_num=table_attributes[9], merge_count=table_attributes[10])
                    self.tables[self.table_names[i]] = name

        else:
            os.mkdir(self.path)
            os.chdir(self.path)

    def close(self):
        # write database metadata to file (table names)
        with open("database.txt", "w") as file:
            file.write(json.dumps(self.table_names))

        # write table metadata to file (all table attributes)
        for table in self.tables.values():
            table.flush_bp()
            table_attributes = []
            table_attributes.append(table.name)
            table_attributes.append(table.num_columns)
            table_attributes.append(table.key)
            table_attributes.append(table.page_directory)
            table_attributes.append(table.rids)
            table_attributes.append(table.tids)
            table_attributes.append(table.page_num)
            table_attributes.append(table.page_range_map)
            table_attributes.append(table.bp_num)
            table_attributes.append(table.tp_num)
            table_attributes.append(table.merge_count)
            # print("PAGE DIR: ", table.page_directory)
            with open(table.name+".txt", "w") as file:
                file.write(json.dumps(table_attributes))

    """
    # Creates a new table
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def create_table(self, name, num_columns, key_index):
        # pass path

        cwd = os.getcwd()
        table_path = os.path.join(cwd, name)
        if os.path.exists(table_path):
            return self.get_table(name)
        else:
            table = Table(name, num_columns, key_index)
            self.tables[name] = table
            self.table_names.append(name)
            os.mkdir(table_path)
            return table

    """
    # Deletes the specified table
    """

    def drop_table(self, name):
        if self.tables.get(name) == None:
            print("Table does not exist")
        else:
            del self.tables[name]
            self.table_names.remove(name)

            cwd = os.getcwd()
            table_path = os.path.join(cwd, name)
            os.remove(table_path)

    """
    # Returns table with the passed name
    """

    def get_table(self, name):
        if self.tables.get(name) == None:
            print("Table does not exist")
        else:
            return self.tables[name]
