"""
----------------------------------------
graph: Construct graphs and stuff from data and stuff.
----------------------------------------
"""
import tkinter as tk
from threading import Event
import matplotlib as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Graph:
    canvas = None
    parent = None
    root = None
    ax = None
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
        Graph.ax.text(2, 2, "test123")

        Graph.canvas.draw()
        Graph.changed_plots[changed_label] = False

    @staticmethod
    def run(gui_parent=None, title=None):
        # Reset plot values.
        Graph.data = dict()
        Graph.changed_plots = dict()
        Graph.colors = dict()

        Graph.parent = gui_parent
        Graph.root = tk.Tk() if gui_parent is None else gui_parent.root
        window = Graph.root if gui_parent is None else tk.Toplevel(Graph.root)
        window.title("Graphs")

        figure = plt.figure.Figure()
        Graph.ax = figure.add_subplot(111)
        if title:
            Graph.ax.set_title(title)

        Graph.canvas = FigureCanvasTkAgg(figure, master=window)
        Graph.canvas.draw()
        Graph.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        Graph.root.after(200, Graph.check_change)

        if gui_parent is None:
            Graph.root.geometry("800x600")
            Graph.root.bind("<Destroy>", lambda e: Graph.close())
            tk.mainloop()

    @staticmethod
    def plot_data(graph_name, X, Y, x_label, y_label):
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
        if Graph.root is None: # Graph window has not been initialized.
            return
        # Create the figure we desire to add to an existing canvas
        p_x, p_y = None, None
        try:
            p_x, p_y = Graph.data[graph_name]
            if X is None:
                X = p_x[-1] + 1
            p_x.append(X)
            p_y.append(Y)
        except KeyError:
            if X is None:
                X = [1]
            elif type(X) is not list:
                X = [X]
            if type(Y) is not list:
                Y = [Y]
            p_x, p_y = X, Y
            Graph.colors[graph_name] = Graph.color_options[len(Graph.data)]
            Graph.data[graph_name] = p_x, p_y

        Graph.ax.set_xlabel(x_label)
        Graph.ax.set_ylabel(y_label)

        Graph.changed_plots[graph_name] = True

    @staticmethod
    def close():
        Graph.root.destroy()
        Graph.stop_event.set()
