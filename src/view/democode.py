from tkinter import *

import tkinter as tk
def getorigin(eventorigin):
      global x,y
      x = eventorigin.x
      y = eventorigin.y
      print(x,y)

root = tk.Tk()
root.bind("<Button 1>",getorigin)

# create the canvas, size in pixels
canvas = Canvas(width=500, height=500, bg='white')

# pack the canvas into a frame/form
canvas.pack(expand=YES, fill=BOTH)

# load the .gif image file
a1 = PhotoImage(file='pcs_bl.png')
# a2 = PhotoImage(file='pcs_bl_t.png')
# b1 = PhotoImage(file='pcs_wh.png')
# b2 = PhotoImage(file='pcs_wh_t.png')

# put gif image on canvas
# pic's upper left corner (NW) on the canvas is at x=50 y=10
# x = 50
# canvas.create_image(10, 10, image=a1, anchor=NW)
# x = x+10
# canvas.create_image(10, 70, image=a2, anchor=NW)
# x = x+50
# canvas.create_image(10, 130, image=b1, anchor=NW)
# x = x+50
# canvas.create_image(10, 190, image=b2, anchor=NW)

def field(x, y, canvas, img) :
    canvas.create_image(x, y, image=img, anchor=NW)

field(10, 10, canvas, a1)

# run it ...
mainloop()