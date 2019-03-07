"""
----------------------------------------
graph: Construct graphs and stuff from data and stuff.
----------------------------------------
"""
import tkinter as tk
from threading import Event, Lock
import matplotlib as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Graph:
    size = (900, 500)
    persist = False
    data = dict()
    changed_plots = dict()
    color_options = ["r", "b", "g", "y"]
    colors = dict()
    stop_event = Event()

    def __init__(self, title, gui_parent=None, x_label=None, y_label=None, pos=None):
        self.persist = True # Set to False if graph should reset between every game.
        self.parent = gui_parent
        self.root = tk.Tk() if gui_parent is None else gui_parent.root
        window = self.root if gui_parent is None else tk.Toplevel(self.root)

        x, y = self.get_window_pos(pos)
        window.geometry("{}x{}+{}+{}".format(self.size[0], self.size[1], x, y))
        window.title(title)

        figure = plt.figure.Figure()
        self.ax = figure.add_subplot(111)
        if title:
            self.ax.set_title(title)
        if x_label:
            self.ax.set_xlabel(x_label)
        if y_label:
            self.ax.set_ylabel(y_label)

        self.canvas = FigureCanvasTkAgg(figure, master=window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.root.protocol("WM_DELETE_WINDOW", lambda: self.close())

    def get_window_pos(self, pos):
        ww, wh = self.size
        if pos:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            if pos == "top-r":
                return (sw - ww-10, -5)
            elif pos == "bot-r":
                return (sw - ww-10, sh - wh-60)
            elif pos == "bot-l":
                return (10, sh - wh-10)
        return (100, 100)

    def run(self):
        """
        Start the mainloop of the underlying
        Tkinter window for this graph.
        """
        tk.mainloop()

    def check_change(self):
        """
        This function is run every 200 ms. by the
        Tkinter mainloop. This function checks for
        incoming data and plots it.
        """
        changed_label = None
        for label in self.changed_plots:
            if self.changed_plots[label]:
                changed_label = label
                break

        if changed_label is None:
            return

        p_x, p_y = self.data[changed_label]

        self.ax.plot(p_x, p_y, self.colors[changed_label])
        self.ax.legend([l for l in self.data])

        self.canvas.draw()
        self.changed_plots[changed_label] = False

    def clear(self):
        # Reset graph window.
        self.data = dict()
        self.changed_plots = dict()
        self.colors = dict()

        self.ax.clear()

    def plot_data(self, graph_name, X, Y):
        """
        Plot data for graph with a given name and axes labels.
        @param graph_name - Name of the graph.
        If it exists, data is added to it, if not a new graph is created.
        @param X - X-axis value(s). Can be a singular value or a list.
        If X is None, the previous X-value for graph with graph_name is
        used instead, and is incremented by one. If no such graph exists,
        X is instantiated to 1.
        @param Y - Y-axis value(s). Can be a singular value or a list.
        @param x_label - Label for x-axis.
        @param y_label - Label for y-axis.
        """
        lock = Lock() # Use a lock (mutex) to ensure thread safety.
        lock.acquire()
        try:
            p_x, p_y = self.data[graph_name]
            if not isinstance(Y, list):
                Y = [Y]
            if X is None:
                X = [v for v in range(p_x[-1]+1, p_x[-1]+1+len(Y))]
            elif not isinstance(X, list):
                X = [X]
            p_x.extend(X)
            p_y.extend(Y)
        except KeyError:
            if not isinstance(Y, list):
                Y = [Y]
            if X is None:
                X = [v for v in range(1, len(Y)+1)]
            elif not isinstance(X, list):
                X = [X]
            self.colors[graph_name] = self.color_options[len(self.data)]
            self.data[graph_name] = (X, Y)

        self.changed_plots[graph_name] = True
        lock.release()

    def close(self):
        self.root.destroy()
        self.stop_event.set()

class GraphHandler:
    """
    GraphHandler acts as a static factory class for
    interacting with any number of graph windows.
    Graphs can be created and closed, and data can be
    added, without worrying about threading issues.
    """
    graphs = dict()

    @staticmethod
    def update_graphs(root_graph):
        for graph in GraphHandler.graphs.values():
            graph.check_change()
        root_graph.root.after(200, lambda g: GraphHandler.update_graphs(g), root_graph)

    @staticmethod
    def new_graph(title, gui_parent=None, x_label=None, y_label=None):
        positions = ["top-r", "bot-r", "bot-l"]
        graph = Graph(title, gui_parent, x_label, y_label, positions[len(GraphHandler.graphs)])
        GraphHandler.graphs[title] = graph
        graph.root.after(200, lambda g: GraphHandler.update_graphs(g), graph)
        return graph

    @staticmethod
    def plot_data(graph_window, graph_name, X, Y):
        GraphHandler.graphs[graph_window].plot_data(graph_name, X, Y)

    @staticmethod
    def close_graphs():
        for graph in GraphHandler.graphs.items():
            graph.close()

    @staticmethod
    def closed():
        for graph in GraphHandler.graphs.items():
            if graph.stop_event.is_set():
                return True
        return False
