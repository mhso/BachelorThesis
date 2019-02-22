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
    canvas = None
    parent = None
    root = None
    ax = None
    persist = False
    data = dict()
    changed_plots = dict()
    color_options = ["r", "b", "g", "y"]
    colors = dict()
    stop_event = Event()

    @staticmethod
    def check_change():
        changed_label = None
        for label in Graph.changed_plots:
            if Graph.changed_plots[label]:
                changed_label = label
                break

        Graph.root.after(100, Graph.check_change)

        if changed_label is None:
            return

        p_x, p_y = Graph.data[changed_label]

        Graph.ax.plot(p_x, p_y, Graph.colors[changed_label])
        Graph.ax.legend([l for l in Graph.data])

        Graph.canvas.draw()
        Graph.changed_plots[changed_label] = False

    @staticmethod
    def run(gui_parent=None, title=None, x_label=None, y_label=None):
        Graph.persist = True # Set to False if graph should reset between every game.
        Graph.parent = gui_parent
        Graph.root = tk.Tk() if gui_parent is None else gui_parent.root
        window = Graph.root if gui_parent is None else tk.Toplevel(Graph.root)
        window.title("Graphs")

        figure = plt.figure.Figure()
        Graph.ax = figure.add_subplot(111)
        if title:
            Graph.ax.set_title(title)
        if x_label:
            Graph.ax.set_xlabel(x_label)
        if y_label:
            Graph.ax.set_ylabel(y_label)

        Graph.canvas = FigureCanvasTkAgg(figure, master=window)
        Graph.canvas.draw()
        Graph.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        Graph.root.after(200, Graph.check_change)

        if gui_parent is None:
            Graph.root.geometry("800x600")
            Graph.root.protocol("WM_DELETE_WINDOW", lambda: Graph.close())
            tk.mainloop()

    @staticmethod
    def clear():
        # Reset graph window.
        Graph.data = dict()
        Graph.changed_plots = dict()
        Graph.colors = dict()

        Graph.ax.clear()

    @staticmethod
    def plot_data(graph_name, X, Y):
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
            p_x, p_y = Graph.data[graph_name]
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
            Graph.colors[graph_name] = Graph.color_options[len(Graph.data)]
            Graph.data[graph_name] = (X, Y)

        Graph.changed_plots[graph_name] = True
        lock.release()

    @staticmethod
    def close():
        Graph.root.destroy()
        Graph.stop_event.set()
