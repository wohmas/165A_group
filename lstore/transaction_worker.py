from lstore.table import Table, Record
from lstore.index import Index
import threading


class TransactionWorker:

    """
    # Creates a transaction worker object.
    """

    def __init__(self, transactions=[]):
        self.stats = []
        self.transactions = transactions
        self.result = 0
        self.runThread = None

    """
    Appends t to transactions
    """

    def add_transaction(self, t):
        self.transactions.append(t)

    """
    Runs all transaction as a thread
    """

    def run(self):
        self.runThread = threading.Thread(target=self.__run)
        self.runThread.start()
        # here you need to create a thread and call __run

    """
    Waits for the worker to finish
    """

    def join(self):
        if self.runThread == None:
            return
        self.runThread.join()

    def __run(self):
        for index in range(len(self.transactions)):
            # each transaction returns True if committed or False if aborted
            # create a loop here if result is false to run the transaction over and over
            result = self.transactions[index].run()
            self.stats.append(result)
        # stores the number of transactions that committed
        self.result = len(list(filter(lambda x: x, self.stats)))
