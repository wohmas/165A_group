from lstore.page import Page
import os
import threading
import math
from lstore.transaction import Transaction
from lstore.table import Table


class Lock_Manager:
    def __init__(self):
        self.transactionLockMap = {}

    def getLock(self, transaction, lock, type):
        if transaction not in self.transactionLockMap.keys():
            self.transactionLockMap[transaction] = []
        gotLock = False

        if type == "s":
            gotLock = lock.getSharedLock(transaction)
        elif type == "e":
            gotLock = lock.getExclusiveLock(transaction)

        if not gotLock:
            return False

        self.transactionLockMap[transaction].append(lock)
        return True

    def releaseLock(self, transaction, lock):
        if lock.releaseLock(transaction):
            self.transactionLockMap[transaction].remove(lock)
            return True
        return False


class TPLock:
    def __init__(self):
        self.reading_count = 0
        self.Writing_count = 0
        self.reading_transactions = []
        self.writing_transaction = None

        self.lock = threading.Lock()
        self.rlock = threading.RLock()
        self.isLocked = 0  # 0 for not locked, 1 for shread, 2 for exclusive

    def getSharedLock(self, transaction):
        self.rlock.acquire()
        if self.Writing_count == 0 or (self.writing_transaction == transaction):
            self.isLocked = 1
            self.reading_count += 1
            self.reading_transactions.append(transaction)
            self.rlock.release()
            return True
        else:
            self.rlock.release()
            return False

    def getExclusiveLock(self, transaction):
        self.lock.acquire()
        if self.Writing_count == 0 and (self.reading_count == 0 or (self.reading_count == 1 and self.reading_transactions[0] == transaction)):
            self.isLocked = 2
            self.Writing_count += 1
            self.writing_transaction = transaction
            self.lock.release()
            return True
        else:
            self.lock.release()
            return False

    def __releaseSharedLock(self, transaction):
        self.rlock.acquire()
        self.reading_transactions.remove(transaction)
        self.reading_count -= 1
        if self.reading_count == 0:
            self.isLocked = 0
        self.rlock.release()
        return True

    def __releaseExclusiveLock(self):
        self.lock.acquire()
        self.isLocked = 0
        self.writing_transaction = None
        self.Writing_count -= 1
        self.lock.release()
        return True

    def releaseLock(self, transaction):
        if transaction not in self.reading_transactions and transaction != self.writing_transaction:
            return False
        if transaction in self.reading_transactions:
            self.__releaseSharedLock(transaction)
        if transaction == self.writing_transaction:
            self.__releaseExclusiveLock()
        return False
