from lstore.page import Page
import os
import threading
import math
from lstore.transaction import Transaction
from lstore.table import Table

class Lock_Manager:
    def __init__(self):
        self.transactionLockMap = {}
    
    def getLock(self, transaction, lock):
        if transaction not in self.transactionLockMap.keys():
            self.transactionLockMap[transaction] = []
        self.transactionLockMap[transaction].append(lock)
        return True
    
    def releaseLock(self, transaction, lock):
        if lock.releaseLock():
            self.transactionLockMap[transaction].remove(lock)
            return True
        return False
        

class TPLock:
    def __init__(self):
        self.reading_count = 0
        self.Writing_count = 0
        self.lock = threading.Lock()
        self.rlock = threading.RLock()
        self.isLocked = 0 # 0 for not locked, 1 for shread, 2 for exclusive
        
    def getSharedLock(self):
        self.rlock.acquire()
        if self.Writing_count == 0:
            self.isLocked=1
            self.reading_count+=1
            self.rlock.release()
            return True
        else:
            self.rlock.release()
            return False
    
    def getExclusiveLock(self):
        self.lock.acquire()
        if self.Writing_count == 0 and self.reading_count == 0:
            self.isLocked=2
            self.Writing_count += 1
            self.lock.release()
            return True
        else:
            self.lock.release()
            return False
        
    def __releaseSharedLock(self):
        self.rlock.acquire()
        self.reading_count-=1
        if self.reading_count == 0:
            self.isLocked=0
        self.rlock.release()
        return True
        
    def __releaseExclusiveLock(self):
        self.lock.acquire()
        self.isLocked=0
        self.Writing_count -= 1
        self.lock.release()
        return True
    
    def releaseLock(self):
        if self.isLocked == 0:
            return False
        if self.isLocked == 1:
            self.__releaseSharedLock()
            return True
        self.__releaseExclusiveLock()
        return True
