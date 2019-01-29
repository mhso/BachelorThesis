import threading
import queue
import tkinter as tk


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
    root = None
    canvas = None
    label = ""
    def __init__(self, observable):
        threading.Thread.__init__(self)
        observable.register_observer(self)
        print("Observer is running in seperate thread")
    
    def notify(self, observable, *args, **kwargs):
        print('Got', args, kwargs, 'From', observable)
        # msg = args[0]
        # self.canvas.create_text(90,45, fill="black", font="Courier 20", text=msg, anchor=tk.NW)
        if args[0] == 10:
            print("whoo")
            self.lets_make_a_move(observable)
            

    
    def run(self):
        print("Observer run")
        self.init_window()
    
    def lets_make_a_move(self, observable):
        observable.gui_says_what("Hey stop ya bastard")
        msg = "you"
        self.canvas.delete(self.label)
        self.canvas.create_text(90,45, fill="black", font="Courier 20", text=msg, anchor=tk.NW)
        self.canvas.update()

    def init_window(self):
        self.root = tk.Tk()
        self.root.title("Latrunculi - The Game")
        self.canvas = tk.Canvas(self.root,width=200,height=100, background='lightgray')
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)
        msg = "hej"
        self.label = self.canvas.create_text(90,45, fill="black", font="Courier 20", text=msg, anchor=tk.NW)
        self.root.mainloop()


    


game = Observable()

gui = Observer(game)
gui.start()


while(game.i < 15) :
    game.increment()