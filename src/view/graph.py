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
    persist = False
    save_to_file = True

    def __init__(self, title, gui_parent=None, same_window=True, x_label=None, y_label=None):
        self.persist = True # Set to False if graph should reset between every game.
        self.data = dict()
        self.changed_plots = dict()
        self.color_options = ["r", "b", "g", "y"]
        self.colors = dict()
        self.stop_event = Event()
        self.parent = gui_parent
        self.root = tk.Tk() if gui_parent is None else gui_parent.root
        w, h, x, y = self.get_window_geometry("top-r")
        inches_h = (h * 0.4) / 80
        inches_w = (w * 0.4) / 80
        figure = plt.figure.Figure(figsize=(inches_w, inches_h))
        self.ax = figure.add_subplot(111)
        self.ax.grid(which="both", axis="both")
        if title:
            self.ax.set_title(title)
        if x_label:
            self.ax.set_xlabel(x_label)
        if y_label:
            self.ax.set_ylabel(y_label)

        self.canvas = FigureCanvasTkAgg(figure, master=self.root)

        self.canvas.draw()

        figure.set_size_inches(inches_w, inches_h, forward=True)
        self.root.geometry("{}x{}+{}+{}".format(w, h, x, y))
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.close())

    def get_window_geometry(self, pos):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww, wh = int(sw // 1.7), int(sh / 1.085)
        x, y = 100, 100
        if pos:
            if pos == "top-r":
                x = sw - ww - 10
                y = -5
            elif pos == "bot-r":
                x = sw - ww - 10
                y = sh - wh - 70
            elif pos == "bot-l":
                x = 10
                y = sh - wh - 10
        return (ww, wh, x, y)

    def run(self):
        """
        Start the mainloop of the underlying
        Tkinter window for this graph.
        """
        self.root.title("Graphs")
        tk.mainloop()

    def check_change(self):
        """
        This function is run every 200 ms. by the
        Tkinter mainloop. This function checks for
        incoming data and plots it.
        """
        changed_labels = []
        for label in self.changed_plots:
            if self.changed_plots[label]:
                changed_labels.append(label)

        if changed_labels == []:
            return False

        handles, labels = self.ax.get_legend_handles_labels()

        for label in changed_labels:
            p_x, p_y = self.data[label]
            
            if label in labels:
                self.ax.plot(p_x, p_y, self.colors[label])
            else:
                self.ax.plot(p_x, p_y, self.colors[label], label=label)
            self.ax.legend()

            self.canvas.draw()
            self.changed_plots[label] = False

        return True

    def save_as_image(self, game_name):
        title = self.ax.get_title().lower().replace(" ", "_")
        self.ax.get_figure().savefig(f"../resources/{game_name}/graph_{title}.png")

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
    def update_graphs(root_graph, game_name):
        for graph in GraphHandler.graphs.values():
            if graph.check_change():
                graph.save_as_image(game_name)
        root_graph.root.after(200, lambda g: GraphHandler.update_graphs(g, game_name), root_graph)

    @staticmethod
    def new_graph(title, game_name, gui_parent=None, x_label=None, y_label=None, same_window=True):
        graph = Graph(title, gui_parent, same_window, x_label, y_label)
        if len(GraphHandler.graphs) < 2:
            graph.canvas.get_tk_widget().grid(row=len(GraphHandler.graphs), column=0)
        else:
            graph.canvas.get_tk_widget().grid(row=len(GraphHandler.graphs)-2, column=1)
        GraphHandler.graphs[title] = graph
        graph.root.after(200, lambda g: GraphHandler.update_graphs(g, game_name), graph)
        return graph

    @staticmethod
    def plot_data(graph_window, graph_name, X, Y):
        try:
            GraphHandler.graphs[graph_window].plot_data(graph_name, X, Y)
        except KeyError:
            return

    @staticmethod
    def close_graphs():
        for graph in GraphHandler.graphs.items():
            graph.close()

    @staticmethod
    def closed():
        for graph in GraphHandler.graphs.values():
            if graph.stop_event.is_set():
                return True
        return False
