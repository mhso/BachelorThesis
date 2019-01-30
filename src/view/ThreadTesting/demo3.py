import queue
import threading
import urllib.request
import time
 
hosts = ["http://yahoo.com", "http://google.com"]
 
queue = queue.Queue()
 
class ThreadUrl(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, queue):
      threading.Thread.__init__(self)
      self.queue = queue

    def run(self):
      while True:
        #grabs host from queue
        host = self.queue.get()
      
        #grabs urls of hosts and prints first 1024 bytes of page
        url = urllib.request.urlopen(host)
        print(url.read(1024))
        print("\n\n")
      
        #signals to queue job is done
        self.queue.task_done()
 
start = time.time()
def main():

  #spawn a pool of threads, and pass them queue instance 
  for _ in range(5):
    t = ThreadUrl(queue)
    t.setDaemon(True)
    t.start()
      
  #populate queue with data   
    for host in hosts:
      queue.put(host)

    #wait on the queue until everything has been processed     
    queue.join()
 
main()
print ("Elapsed Time: %s" % (time.time() - start))