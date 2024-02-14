


import tkinter as tk

class MarkerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Marker App")
        self.coordinates_marker =[]

        self.canvas = tk.Canvas(self.master, width=400, height=400, bg="white")
        self.canvas.pack()

        self.marker = self.canvas.create_oval(50, 50, 70, 70, fill="red", tags="marker")
        self.canvas.tag_bind("marker", "<B1-Motion>", self.move_marker)
        self.canvas.tag_bind("marker", "<ButtonRelease-1>", self.release_marker)



    def move_marker(self, event):
        # Move the marker with the mouse

        self.canvas.coords(self.marker, event.x - 10, event.y - 10, event.x + 10, event.y + 10)

        x1, y1, x2, y2 = self.canvas.coords(self.marker)

        self.coordinates_marker = [((x1+x2)/2), ((y1+y2)/2)]
        print(f'coordinates_marker: {self.coordinates_marker}')

    def release_marker(self, event):
        # Perform actions on marker release if needed
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = MarkerApp(root)
    root.mainloop()
