"""
----------------------------------------
graph: Construct graphs and stuff from data and stuff.
----------------------------------------
"""
import matplotlib as plt
import numpy as np
import tkinter as tk
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg

class Graph:
    canvas = None

    def __init__(self, gui_parent=None):
        self.parent = gui_parent

    def draw_to_canvas(self, figure):
        fcagg = FigureCanvasAgg(figure)
        fcagg.draw()
        x, y, w, h = figure.bbox.bounds()
        w, h = int(w), int(h)
        img = tk.PhotoImage(master=self.canvas, width=w, height=h)

        self.canvas.create_image(w/2, h/2, image=img)
        
        tkagg.blit(img, fcagg.get_renderer()._renderer, colormode=2)

        return img

    def start(self):
        window = tk.Toplevel() if self.parent else tk.Tk()
        window.title("Graph stuff")
        self.canvas = tk.Canvas(window, width=500, height=350)
        self.canvas.pack()

        
