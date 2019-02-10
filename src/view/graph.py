"""
----------------------------------------
graph: Construct graphs and stuff from data and stuff.
----------------------------------------
"""
import tkinter as tk
import matplotlib as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Event

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

        Graph.canvas.draw()
        Graph.changed_plots[changed_label] = False

    @staticmethod
    def run(gui_parent=None):
        Graph.parent = gui_parent
        Graph.root = tk.Tk() if gui_parent is None else gui_parent.root
        window = Graph.root if gui_parent is None else tk.Toplevel(Graph.root)
        window.title("Graphs")

        figure = plt.figure.Figure()
        Graph.ax = figure.add_subplot(111)

        Graph.canvas = FigureCanvasTkAgg(figure, master=window)
        Graph.canvas.draw()
        Graph.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        Graph.root.after(200, Graph.check_change)

        if gui_parent is None:
            Graph.root.geometry("800x600")
            Graph.root.bind("<Destroy>", lambda e: Graph.close())
            tk.mainloop()

    @staticmethod
    def plot_data(X, Y, label, x_label, y_label):
        if Graph.root is None: # Graph window has not been initialized.
            return
        # Create the figure we desire to add to an existing canvas
        p_x, p_y = None, None
        try:
            p_x, p_y = Graph.data[label]
            if X is None:
                X = p_x[-1] + 1
            p_x.append(X)
            p_y.append(Y)
        except KeyError:
            if X is None:
                X = 1
            p_x, p_y = [X], [Y]
            Graph.colors[label] = Graph.color_options[len(Graph.data)]
            Graph.data[label] = p_x, p_y

        Graph.ax.set_xlabel(x_label)
        Graph.ax.set_ylabel(y_label)

        Graph.changed_plots[label] = True

    @staticmethod
    def close():
        Graph.root.destroy()
        Graph.stop_event.set()
