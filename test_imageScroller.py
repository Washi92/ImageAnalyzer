import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tk_file
from PIL import ImageTk, Image
import os

app = tk.Tk()
app.geometry("700x800")
app.resizable(False, False)

def pop_menu(e):
    menu_bar.tk_popup(x=e.x_root, y=e.y_root)


img_list = []
img_vars = []

def display_images(index):
    img_display_lb.config(image=img_list[index][1])

def load_images():
    dir_path = tk_file.askdirectory()

    img_files = os.listdir(dir_path)
    for r in range(0, len(img_files)):
        img_list.append([
            ImageTk.PhotoImage(Image.open(os.path.join(dir_path, img_files[r])).
                               resize((50,50),  Image.Resampling.LANCZOS)),
            ImageTk.PhotoImage(Image.open(os.path.join(dir_path, img_files[r])).
                               resize((480,360), Image.Resampling.LANCZOS))
        ])
        img_vars.append(f'img_{r}')

    for n in range(len(img_vars)):
        globals()[img_vars[n]] = tk.Button(slider, image=img_list[n][0], bd=0,
                                           command=lambda n=n: display_images(n))
        globals()[img_vars[n]].pack(side=tk.LEFT)



#Button
menu_btn = tk.Button(app, text="Menu", bd=0, font=("Bold",15))
menu_btn.pack(side=tk.TOP, anchor=tk.W, pady=5, padx=5)
menu_btn.bind("<Button-1>", pop_menu)

#MenuBar
menu_bar = tk.Menu(app, tearoff=False)
menu_bar.add_command(label="Open Folder", command=load_images)

#Images section
img_display_lb = tk.Label(app)
img_display_lb.pack(anchor=tk.CENTER)

canvas = tk.Canvas(app, width=700, height=80)
canvas.pack(side=tk.BOTTOM, fill=tk.X)

#Scroll bar
x_scrollbar = ttk.Scrollbar(app, orient=tk.HORIZONTAL)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
x_scrollbar.config(command=canvas.xview)

canvas.config(xscrollcommand=x_scrollbar.set)
canvas.bind("<Configure>", lambda e: canvas.bbox('all'))

#Section for images loaded
slider = tk.Frame(canvas)
canvas.create_window((0,0), window=slider, anchor=tk.NW)

app.mainloop()