import urllib.request
import time
 
hosts = ["http://yahoo.com", "http://google.com", "http://gmail.cp,",
"http://mhooge.com", "http://tdc.dk"]
 
start = time.time()
#grabs urls of hosts and prints first 1024 bytes of page
for host in hosts:
  url = urllib.request.urlopen(host)
  print(url.read(1024))
  print("\n\n")

print("Elapsed Time: %s" % (time.time() - start))