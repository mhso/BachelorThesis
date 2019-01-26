import tkinter as tk
import pickle
from glob import glob

active_nodes = []
base_nodes = []
model = None

root = tk.Tk("Draw MCTS")
main_canvas = tk.Canvas(root, width=1280, height=720, background='lightgray')
main_canvas.pack(expand=tk.YES, fill=tk.BOTH)

main_canvas.create_text((main_canvas.winfo_reqwidth()/2), 40, text="Root States", font="Courier 20")

def draw_nodes(nodes, canvas):
    global active_nodes
    canvas.create_rectangle(0, 60, canvas.winfo_reqwidth(), canvas.winfo_reqheight(), fill="lightgray")
    gap_x = 30
    top_y = 50
    gap_y = 30
    row = 1
    col = 1

    for node in nodes:
        x = col * gap_x
        if x > canvas.winfo_reqwidth() - 50:
            x = gap_x
            row += 1
            col = 0
        y = top_y+(gap_y*row)
        active_nodes.append(((x, y), node))
        col += 1
        draw_node(node, x, y, 25, canvas)

def on_click(origin):
    global active_nodes, main_canvas, base_nodes
    x = origin.x
    y = origin.y
    for (nx, ny), node in active_nodes:
        if x > nx and y > ny and x < nx+30 and y < ny+30:
            show_node_view(node)
            draw_nodes(base_nodes, main_canvas)
            break

def draw_state(state, canvas):
    canvas.create_text((canvas.winfo_reqwidth()/2), 200, text="Player: " + ("White" if state.player else "Black"), font="Courier 20")
    canvas.create_text((canvas.winfo_reqwidth()/2), 300, text="Board", font="Courier 20")
    canvas.create_text((canvas.winfo_reqwidth()/2), 400, text=str(state.board), font="Courier 12")

def show_node_view(node):
    global active_nodes, model
    active_nodes = []
    node_window = tk.Toplevel(width=600, height=500)

    node_canvas = tk.Canvas(node_window, width=600, height=500, background='lightgray')
    node_canvas.pack(expand=tk.YES, fill=tk.BOTH)

    draw_nodes(node.children, node_canvas)
    node_canvas.create_text((node_canvas.winfo_reqwidth()/2), 40, text="Node Children", font="Courier 20")
    node_canvas.create_text((node_canvas.winfo_reqwidth()/2), 230, text="Visits: " + str(node.visits), font="Courier 20")
    node_canvas.create_text((node_canvas.winfo_reqwidth()/2), 260, text="Wins: " + str(node.wins), font="Courier 20")
    draw_state(node.state, node_canvas)

    node_window.bind("<Button 1>", on_click);

def draw_node(node, x, y, size, canvas):
    canvas.create_oval(x, y, x+size, y+size, fill='lightblue')

root.bind("<Button 1>", on_click);
newest = glob("../resources/mcts*")[-1]

try:
    model = pickle.load(open(newest, "rb"))
    nodes = [model[k] for k in model]
    base_nodes = [node for node in nodes]
    draw_nodes(nodes, main_canvas)
    root.mainloop()
except IOError:
    print("No model found from file")
