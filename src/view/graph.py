"""
----------------------------------------
graph: Construct graphs and stuff from data and stuff.
----------------------------------------
"""
import tkinter as tk
import matplotlib as plt
from matplotlib.backends import tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg

class Graph:
    canvas = None

    def __init__(self, gui_parent=None):
        self.parent = gui_parent

    def draw_to_canvas(self, figure, loc):
        fcagg = FigureCanvasAgg(figure)
        fcagg.draw()
        x, y, w, h = figure.bbox.bounds()
        w, h = int(w), int(h)
        img = tk.PhotoImage(master=self.canvas, width=w, height=h)

        self.canvas.create_image(loc[0] + (w/2), loc[1] + (h/2), image=img)

        tkagg.blit(img, fcagg.get_renderer()._renderer, colormode=2)

        return img

    def start(self):
        window = tk.Toplevel() if self.parent else tk.Tk()
        window.title("Graph stuff")
        self.canvas = tk.Canvas(window, width=500, height=350)
        self.canvas.pack()

    def plot(self, X, Y):
        # Create the figure we desire to add to an existing canvas
        fig = plt.figure.Figure(figsize=(2, 1))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.plot(X, Y)

        fig_x, fig_y = 10, 10
        fig_img = self.draw_to_canvas(fig, (fig_x, fig_y))
