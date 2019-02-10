import threading
import time
import numpy as np

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter, list1, board):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      self.workwork(list1, board)
   
    def workwork(self, list, board):
        for r  in range(board.shape[0]):
            for c in range(board.shape[1]):
                if board[r, c] %2 == 0:
                    list.append((r, c))

    def run(self):
      print("Starting " + self.name)
      # Get lock to synchronize threads
      threadLock.acquire()
      # Free lock to release next thread
      threadLock.release()


board = np.array([[0,1,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16],[0,1,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])

threadLock = threading.Lock()
threads = []

list = []
list1 = []
list2 = []
list3 = []
list4 = []

# Create new threads
thread1 = myThread(1, "Thread-1", 1, list1, board)
thread2 = myThread(2, "Thread-2", 2, list2, board)
thread3 = myThread(1, "Thread-1", 1, list3, board)
thread4 = myThread(2, "Thread-2", 2, list4, board)

# Start new Threads
thread1.start()
thread2.start()
thread3.start()
thread4.start()

# Add threads to thread list
threads.append(thread1)
threads.append(thread2)
threads.append(thread3)
threads.append(thread4)

list.extend(list1)
list.extend(list2)
list.extend(list3)
list.extend(list4)

print("List 1 contains {} elements".format(len(list1)))
print("List 2 contains {} elements".format(len(list2)))
print("List 3 contains {} elements".format(len(list3)))
print("List 4 contains {} elements".format(len(list4)))


# Wait for all threads to complete
for t in threads:
    t.join()
print("Exiting Main Thread")
print("List contains {} elements".format(len(list)))