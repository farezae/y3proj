#using matplotlib with tkinter

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
style.use('seaborn-v0_8')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import * 



root = Tk()
root.title("test")

root.minsize(200, 200) 
root.maxsize(500, 500)
root.geometry("300x300+50+50")  


frame = Frame(root)
frame.pack() 

f = plt.figure() 
a = f.add_subplot(1,1,1)

def animate(i):
    graph_data = open('example.txt','r').read()
    lines = graph_data.split('\n')
    xs = []
    ys = []
    for line in lines:
        if len(line) > 1:
            x, y = line.split(',')
            xs.append(float(x))
            ys.append(float(y))
    a.clear()
    a.plot(xs, ys)


ani = animation.FuncAnimation(f, animate, interval=1000)    
canvas = FigureCanvasTkAgg(f,frame)
canvas.draw() 
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)




root.mainloop()
