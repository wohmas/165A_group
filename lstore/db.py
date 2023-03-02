from lstore.table import Table
import os


class Database():

    def __init__(self):
        self.tables = []
        self.path = ""
        pass

    def open(self, path):
        cwd = os.getcwd()
        self.path = os.path.join(cwd, path)
        os.mkdir(self.path)
        pass

    def close(self):
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
        pass
