import threading
import queue

queue = queue.Queue()

class Observable():
    i = 0

    def __init__(self):
        self.__observers = []
        print("Observable is running in main thread")
    
    def register_observer(self, observer):
        self.__observers.append(observer)
    
    def notify_observers(self, *args, **kwargs):
        for observer in self.__observers:
            observer.notify(self, *args, **kwargs)
    def increment(self):
        self.i = self.i + 1
        self.notify_observers(self.i)
    
    def gui_says_what(self, str):
        print("gui_says_what:")
        print(str)

class Observer(threading.Thread):
    
    def __init__(self, observable):
        threading.Thread.__init__(self)
        observable.register_observer(self)
        print("Observer is running in seperate thread")
    
    def notify(self, observable, *args, **kwargs):
        print('Got', args, kwargs, 'From', observable)
        if args[0] == 10:
            print("whoo")
            self.lets_make_a_move(observable)

    
    def run(self):
        print("Observer run")
    
    def lets_make_a_move(self, observable):
        observable.gui_says_what("Hey stop ya bastard")

    


game = Observable()

gui = Observer(game)
gui.start()


while(game.i < 15) :
    game.increment()