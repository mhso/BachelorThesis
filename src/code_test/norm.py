import time
import multiprocessing 

class Par():
    main_list = []
    def basic_func(self, x):
        if x == 0:
            return 'zero'
        elif x%2 == 0:
            return 'even'
        else:
            return 'odd'

    def nonmultiprocessing_func(self, x):
        y = x*x
        print('{} squared results in a/an {} number'.format(x, self.basic_func(y)))

    def append(self, n, main_list):
        mylist = []
        for i in range(1,100):
            mylist.append("Thread {}, val: {}".format(n,i*n))
            #print("Thread {}, val: {}".format(n,i*n))
        main_list.extend(mylist)


    def norm(self):
        starttime = time.time()

        for i in range(1,5):
            self.append(i, self.main_list)
            
        print("List lenght: {}".format(len(self.main_list)))
        # for i in self.main_list:
        #     print(i)
        print('That took {} seconds'.format(time.time() - starttime))

par = Par()

par.norm()