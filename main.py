import os
import tkinter as tk
from tkinter import filedialog, ttk
import customtkinter
from PIL import Image, ImageTk

# Libs for mathematical computations
import numpy as np
from scipy import interpolate
from scipy.spatial.distance import euclidean
import json
import copy

SPACING = 10
RESIZE_IMG_WIDTH = 150
MAX_LANDMARK_NB = 3
SIZE_LANDMARK = 10
#######
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
LEFT_FRAMES_WIDTH = 300
RIGHT_FRAMES_WIDTH = SCREEN_WIDTH - LEFT_FRAMES_WIDTH
TOP_FRAMES_HEIGHT = 600
#######

class ImageApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Analyzer")
        # Calculate the position to center the window
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        x_position = (screen_width - SCREEN_WIDTH) // 2
        y_position = (screen_height - SCREEN_HEIGHT) // 2
        self.master.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+{x_position}+{y_position}")

        self.master.resizable(False,False)

        # List to store loaded images
        self.images = []
        self.image_markers = {}
        self.images_and_markers = {}
        self.current_img_name =""

        self.f_imgs = []

        # Local variables
        self.pen_color = "red"
        self.pen_size = 5
        self.x_points = []
        self.y_points = []
        self.points = []

        # For positioning landmarks
        self.coordinates_marker = []
        self.landmarks = []#[None] * MAX_LANDMARK_NB

        # For drawing curved lines
        self.c_points = []
        self.c_lines = []



        self.length_pixel_ratio = customtkinter.IntVar(value=10)
        self.curve_resolution = customtkinter.IntVar(value=50)


        customtkinter.set_appearance_mode("system")

        # Create main frames to split the screen in left and right side sides
        left_frame = customtkinter.CTkFrame(master=self.master)
        left_frame.pack(side="left", anchor="nw")
        right_frame = customtkinter.CTkFrame(master=self.master)
        right_frame.pack(side="right")

        # Frames to display the loaded images
        left_up_frame = customtkinter.CTkFrame(master=left_frame)
        left_up_frame.pack(side="top", fill="y", expand=True, anchor="nw")
        # Associate a Scrollbar to the left_up_frame
        self.scrollbar = customtkinter.CTkScrollbar(left_up_frame, orientation="vertical")
        self.scrollbar.pack(side="right", fill="y")

        left_down_frame = customtkinter.CTkFrame(master=left_frame, width=LEFT_FRAMES_WIDTH,
                                                 height=SCREEN_HEIGHT - TOP_FRAMES_HEIGHT)
        left_down_frame.pack(side="bottom", anchor="nw")

        # Frames to analyze the image
        right_up_frame = customtkinter.CTkFrame(master=right_frame, width=SCREEN_WIDTH - LEFT_FRAMES_WIDTH,
                                                height=TOP_FRAMES_HEIGHT)
        right_up_frame.pack(side="top", anchor="nw")

        self.right_down_frame = customtkinter.CTkFrame(master=right_frame, border_color="blue",
                                                       width=SCREEN_WIDTH - LEFT_FRAMES_WIDTH,
                                                       height=SCREEN_HEIGHT - TOP_FRAMES_HEIGHT)
        self.right_down_frame.pack(side="bottom", anchor="nw")

        # Canvas for displaying the loaded images and configure the scrollbar
        self.canvas_left = customtkinter.CTkCanvas(left_up_frame, width=LEFT_FRAMES_WIDTH,
                                                   height=TOP_FRAMES_HEIGHT, background="dark gray")
        self.canvas_left.pack()
        self.canvas_left.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.canvas_left.yview)

        # Canvas for displaying the selected image to analyze
        self.canvas_right = tk.Canvas(right_up_frame, background="dark gray",
                                                    width=SCREEN_WIDTH - LEFT_FRAMES_WIDTH,
                                                    height=TOP_FRAMES_HEIGHT)  # bd=0, highlightthickness=0
        self.canvas_right.pack()





        # Buttons
        load_btn = customtkinter.CTkButton(master=left_down_frame, text="Load Image", command=self.load_images)
        load_btn.place(relx=0.5, rely=0.6, anchor="center")

        create_marker_btn = customtkinter.CTkButton(master=self.right_down_frame, text="Create Marker", state="disabled",
                                             text_color="white",command=self.create_marker)
        create_marker_btn.place(relx=0.25, rely=0.6, anchor="center")

        remove_marker_btn = customtkinter.CTkButton(master=self.right_down_frame, text="Remove Marker",
                                                    state="disabled",
                                                    text_color="white", command=self.remove_marker)
        remove_marker_btn.place(relx=0.25, rely=0.8, anchor="center")

        export_btn = customtkinter.CTkButton(master=self.right_down_frame, text="Export", state="disabled",
                                             text_color="white", width=110,height=110, command=self.export_images_to_json)
        export_btn.place(relx=0.1, rely=0.56, anchor="center")

        curve_btn = customtkinter.CTkButton(master=self.right_down_frame, text="Draw", state="disabled",
                                            text_color="white", width=100, height=20, command=self.draw_curve)
        curve_btn.place(relx=0.5, rely=0.6, anchor="center")

        #TEST BYTTON
        test_btn = customtkinter.CTkButton(master=self.right_down_frame, text="TEST",
                                            text_color="white", width=100, height=20, command=self.test_func)
        test_btn.place(relx=0.5, rely=0.8, anchor="center")

        # Switch function: draw a curve



        def position_marker_switcher():
            if self.position_marker_switch_var.get() == "on":
                # Disable other functionalitites
                self.draw_curve_switch.configure(state="disabled")
                curve_btn.configure(state="disabled")

                # Activate marker functionalitites
                self.position_marker_switch.configure(state="normal")
                export_btn.configure(state="normal")
                create_marker_btn.configure(state="normal")
                remove_marker_btn.configure(state="normal")
                export_btn.configure(state="normal")
                #self.canvas_right.bind("<Button-1>", self.draw_point)

            else:
                #self.canvas_right.unbind("<Button-1>")
                # Remove the points from the canvas
                self.points.clear()
                for p in self.c_points:
                    self.canvas_right.delete(p)
                self.c_points = []

                # Activate other functionalitites
                self.draw_curve_switch.configure(state="normal")


        # Switch for positioning markers
        self.position_marker_switch_var = customtkinter.StringVar(value="off")
        self.position_marker_switch = customtkinter.CTkSwitch(master=self.right_down_frame, text="Place Markers",
                                                         text_color="white",
                                                         variable=self.position_marker_switch_var, onvalue="on", offvalue="off",
                                                         command=position_marker_switcher, state="disabled")

        self.position_marker_switch.place(relx=0.25, rely=0.3, anchor="center")



        # Switch function: draw a curve
        def draw_curve_switcher():
            if self.draw_curve_switch_var.get() == "on":
                # Disable other functionalitites

                export_btn.configure(state="disabled")
                create_marker_btn.configure(state="disabled")
                remove_marker_btn.configure(state="disabled")
                #export_btn.configure(state="disabled")

                self.position_marker_switch_var.set("off")
                self.position_marker_switch.configure(state="disabled")

                # Activate curve functionalitites
                self.draw_curve_switch.configure(state="normal")
                curve_btn.configure(state="normal")
                self.canvas_right.bind("<Button-1>", self.draw_point)

            else:
                curve_btn.configure(state="disabled")
                self.canvas_right.unbind("<Button-1>")
                # Remove labels form the canvas
                self.perimeter_lb.configure(text='')
                self.area_lb.configure(text='')

                # Remove the points from the canvas
                for p in self.c_points:
                    self.canvas_right.delete(p)
                self.c_points = []

                # Remove the curved lines from the canvas
                for l in self.c_lines:
                    self.canvas_right.delete(l)
                self.c_lines = []

                # Activate other functionalitites
                self.position_marker_switch.configure(state="normal")



        self.draw_curve_switch_var = customtkinter.StringVar(value="off")
        self.draw_curve_switch = customtkinter.CTkSwitch(master=self.right_down_frame, text="Draw Curve", text_color="white",
                                                         variable=self.draw_curve_switch_var, onvalue="on", offvalue="off",
                                                         command=draw_curve_switcher, state="disabled")
        self.draw_curve_switch.place(relx=0.50, rely=0.3, anchor="center")



        #Slider for len/pixel
        slider_lp = customtkinter.CTkSlider(master=self.right_down_frame, from_=1, to=100, width=100,
                                             variable=self.length_pixel_ratio)
        slider_lp.place(relx=0.75, rely=0.3, anchor="center")

        # Slider to choose the resolution or the curved lines
        slider_cl = customtkinter.CTkSlider(master=self.right_down_frame, from_=4, to=100, width=100, variable=self.curve_resolution)
        slider_cl.place(relx=0.75, rely=0.6, anchor="center")


        # Labels created only with Draw button pressed
        self.perimeter_lb = customtkinter.CTkLabel(master=right_up_frame, text="")
        self.perimeter_lb.place(relx=0.8, rely=0.05, anchor="center")
        self.area_lb = customtkinter.CTkLabel(master=right_up_frame, text="")
        self.area_lb.place(relx=0.8, rely=0.1, anchor="center")

        self.lenpix_lb = customtkinter.CTkLabel(master=self.right_down_frame, textvariable=self.length_pixel_ratio)
        self.lenpix_lb.place(relx=0.81, rely=0.3, anchor="center")

        self.scale_lb = customtkinter.CTkLabel(master=self.right_down_frame, text="mm/pixel" )
        self.scale_lb.place(relx=0.84, rely=0.3, anchor="center")

        self.c_resolution_lb = customtkinter.CTkLabel(master=self.right_down_frame, textvariable=self.curve_resolution)
        self.c_resolution_lb.place(relx=0.81, rely=0.6, anchor="center")




        # Main Image
        self.main_image_label = tk.Label(self.canvas_right)
        #self.main_image_label.pack(anchor=tk.CENTER)
        #self.main_image_tk = None

        # Image Name Entry
        self.search_entry = customtkinter.CTkEntry(left_down_frame,placeholder_text="Search image", width=300)
        self.search_entry.place(relx=0.5, rely=0.25, anchor="center")
        self.search_entry.bind("<KeyRelease>", self.filtered_images)

    #Adjust the scale line
    #def adjust_line_length(self, event):
        # Clear previous content from the canvas
       # self.canvas_right.delete("line")

        # Draw a little horizontal line in the bottom-left
        #line_length = self.length_pixel_ratio.get()  # Adjust the length of the line as needed
        #line_thickness = 5
        #self.canvas_right.create_line(30, self.canvas_right.winfo_height() - 50, line_length,
         #                             self.canvas_right.winfo_height() - 50, fill="red", width=line_thickness)

    def test_func(self):
        print(f"\n\nTEST")
        print(f"current_img_name: {self.current_img_name}")
        print(f"image_markers: {self.image_markers}")
        print("\nDICTIONARY current_img_name:")

        self.images_and_markers[self.current_img_name] = copy.deepcopy(self.image_markers)

        print(self.images_and_markers)

    def export_images_to_json(self, filename="images.json"):

        print(f"\nEXPORT")
        #Format JSON
        formatted_data = {}
        for image_name, markers in self.images_and_markers.items():
            formatted_markers = {}
            for landmark_id, (x, y) in markers.items():
                formatted_markers[f"Landmark{landmark_id + 1}"] = {"X": x, "Y": y}
            formatted_data[image_name] = formatted_markers

        # Convert the dictionary to JSON format
        data = json.dumps(formatted_data, indent=4)

        # Write the JSON data to a file
        with open(filename, 'w') as json_file:
            json_file.write(data)

    def create_marker(self):
        if len(self.landmarks) >= MAX_LANDMARK_NB:
            return
        print(f"\nCREATING NEW MARKER")
        marker_id = int(len(self.landmarks))
        # create a landmark
        x,y = RIGHT_FRAMES_WIDTH/2, TOP_FRAMES_HEIGHT/2
        marker = self.canvas_right.create_oval(x, y, x+SIZE_LANDMARK, y+SIZE_LANDMARK, fill="blue", tags=f"marker{marker_id}")

        self.landmarks.append(marker)

        #Bind motion to specific marker
        self.canvas_right.tag_bind(f"marker{marker_id}", "<B1-Motion>",
                                   lambda e, m=marker_id: self.move_marker(e, m))
        self.canvas_right.tag_bind(f"marker{marker_id}", "<ButtonRelease-1>",
                                   lambda e, m=marker_id: self.move_marker(e, m))

    def move_marker(self, event, marker_id):
        if self.position_marker_switch_var.get() == "off":
            return
        # Move the marker with the mouse
        self.canvas_right.coords(self.landmarks[marker_id], event.x - 10, event.y - 10, event.x + 10, event.y + 10)

        x1, y1, x2, y2 = self.canvas_right.coords(self.landmarks[marker_id])

        coord_x = (x1+x2)/2
        coord_y = (y1+y2)/2
        self.coordinates_marker.append((coord_x,coord_y))


        #print(f'coordinates_marker for Point {marker_id}: {self.coordinates_marker[-1]}')
        self.image_markers[marker_id] = self.coordinates_marker[-1]

    def remove_marker(self):
        if self.landmarks:
            last_marker_id = len(self.landmarks) - 1
            last_marker = self.landmarks.pop()
            self.canvas_right.delete(last_marker)
            self.coordinates_marker.pop()

        if self.image_markers:
            del self.image_markers[next(reversed(self.image_markers))]

        # Save the current position of markers
        #self.test_func()


    def release_marker(self, event):
        # Perform actions on marker release if needed
        pass
    def draw_point(self, event):

        #if self.position_marker_switch_var.get() == "on" and len(self.points) >= MAX_LANDMARK_NB:
         #   return

        print(f'event.x{event.x} event.y {event.y} ')
        x, y = event.x, event.y


        self.points.append((x, y))
        print(self.points)
        print(f'Number of points: {len(self.points)}')

        x1, y1 = (event.x - self.pen_size), (event.y - self.pen_size)
        x2, y2 = (event.x + self.pen_size), (event.y + self.pen_size)

        # Draw points for each click and keep a reference
        point = self.canvas_right.create_oval(x1, y1, x2, y2, fill=self.pen_color, outline='')
        self.c_points.append(point)

    def draw_curve(self):
        perimeter = 0
        area = 0

        x = np.array([point[0] for point in self.points])
        y = np.array([point[1] for point in self.points])
        print(f'x: {x}, y: {y}')

        # append the starting x,y coordinates
        x = np.r_[x, x[0]]
        y = np.r_[y, y[0]]

        # fit splines to x=f(u) and y=g(u), treating both as periodic. also note that s=0
        # is needed in order to force the spline fit to pass through all the input points.
        tck, u = interpolate.splprep([x, y], s=0, per=True)

        # evaluate the spline fits for points_per_spline evenly spaced distance values
        points_per_spline = self.curve_resolution.get()
        xi, yi = interpolate.splev(np.linspace(0, 1, points_per_spline), tck)

        # Draw the interpolated curve on the canvas
        for i in range(len(xi) - 1):
            x1, y1 = xi[i], yi[i]
            x2, y2 = xi[i + 1], yi[i + 1]

            # Calculate the distance between consecutive points and add to the perimeter
            perimeter += euclidean((x1, y1), (x2, y2))
            # Calculate the contribution to the area using the Shoelace formula
            area += x1 * y2 - x2 * y1

            line = self.canvas_right.create_line(x1, y1, x2, y2, fill='green', width=2)
            self.c_lines.append(line)

        area = abs(area) / 2

        print(f'Original Perimeter: {perimeter}')
        print(f'Original Area: {area}')

        # Convert the results according to the mm/pixel ration
        perimeter = perimeter / self.length_pixel_ratio.get()
        factor = self.length_pixel_ratio.get()
        print(f'factor: {factor}')
        area = area / int(factor ** 2)
        self.perimeter_lb.configure(text=f'Perimeter: {perimeter}')
        self.area_lb.configure(text=f'Area: {area}')


        # Clear points before drawing new curved lines
        self.points.clear()


    def filtered_images(self, event=None):
        self.filter_and_display_images()

    def filter_and_display_images(self):
        # Clear previous images on the canvas
        for widget in self.canvas_left.winfo_children():
            widget.destroy()

        # Filter images based on the entered text
        filter_text = self.search_entry.get().lower()

        y_position = 0
        for i, img in enumerate(self.images):
            img_name = img["image_name"].lower()
            if filter_text in img_name:
                resized_image = img["resized_image"]
                tk_image = ImageTk.PhotoImage(resized_image)

                # Display images on the canvas with spacing
                x_position = 20

                image_label = tk.Label(self.canvas_left, image=tk_image)
                image_label.image = tk_image  # Keep a reference to avoid garbage collection

                # Create a button associated with the current image & display it
                btn_img = tk.Button(self.canvas_left, text=None, image= tk_image,
                                   command=lambda i=i: self.display_main_image(i))

                self.canvas_left.create_window(x_position, y_position, anchor=tk.NW, window=btn_img)


                # Display image info to the right of the image
                info_text = f"Name: {img["image_name"]}\nDimensions: {img["image_size"][0]}x{img["image_size"][1]}"
                info_label = tk.Label(self.canvas_left, text=info_text, anchor=tk.W, justify=tk.LEFT)
                self.canvas_left.create_window(x_position + RESIZE_IMG_WIDTH + SPACING, y_position, anchor=tk.NW, width=210,
                                          window=info_label)

                y_position += resized_image.height + SPACING

        # Update the canvas to show the loaded images

        self.canvas_left.config(scrollregion=self.canvas_left.bbox(tk.ALL))

    def display_main_image(self, image_index):
        print(f"\ndisplay_main_image Image name: {self.images[image_index]["image_name"]}")
        self.current_img_name = self.images[image_index]["image_name"]


        # Clear previous content from the canvas
        self.canvas_right.delete("all")
        # Remove remaining landmarks and points
        self.points.clear()
        print(f"Before cleaning  self.landmarks: {self.landmarks}")
        self.landmarks.clear()
        self.image_markers.clear()




        self.perimeter_lb.configure(text='')
        self.area_lb.configure(text='')

        image_tk = ImageTk.PhotoImage(self.images[image_index]["image"])

        self.canvas_right.image = image_tk
        self.canvas_right.create_image(0, 0, image=image_tk, anchor="nw")

        # Retrieve and display existing larkers
        if bool(self.images_and_markers.get(self.current_img_name, {})):
            self.display_markers(self.current_img_name)
        else:
            print("No markers found!")
            print(f'images_and_markers: {self.images_and_markers}')

        self.draw_curve_switch.configure(state="normal")
        self.position_marker_switch.configure(state="normal")


    def display_markers(self, img_name):
        print("\nDisplaying all markers...")

        print(f'self.images_and_markers: {self.images_and_markers}')

        self.image_markers = self.images_and_markers[img_name]
        print(f'\nMarkers for image on display {img_name}: {self.image_markers}')

        nb_markers = len(self.images_and_markers[img_name])
        #print(f'number of markers: {nb_markers}')

        for i in range(nb_markers):
            print(f'marker {i}: {self.images_and_markers[img_name][i]}')
            x, y = self.images_and_markers[img_name][i]
            x1, y1 = x-SIZE_LANDMARK, y-SIZE_LANDMARK
            x2, y2 = x+SIZE_LANDMARK, y+SIZE_LANDMARK
            print(x1, y1, x2, y2)
            marker = self.canvas_right.create_oval(x1, y1, x2, y2, fill="blue", tags=f"marker{i}")
            self.landmarks.append(marker)
            # Bind motion to specific marker
            self.canvas_right.tag_bind(f"marker{i}", "<B1-Motion>",
                lambda e, m=i: self.move_marker(e, m))
            self.canvas_right.tag_bind(f"marker{i}", "<ButtonRelease-1>",
              lambda e, m=i: self.move_marker(e, m))

        # Save the current position of markers
        self.test_func()




    def load_images(self):
        # Clear the text in the entry
        self.search_entry.delete(0, tk.END)

        # Open a file dialog to select images
        file_paths = filedialog.askopenfilenames(title="Select Images",
                                                 filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])

        for i, file_path in enumerate(file_paths):
            image_name = os.path.basename(file_path)
            if any(img["image_name"] == image_name for img in self.images):
                continue

            loaded_img = Image.open(file_path)


            # Resize image to fit in the left frame
            left_img_resized = loaded_img.resize((RESIZE_IMG_WIDTH,
                                                  int((RESIZE_IMG_WIDTH / loaded_img.width) * loaded_img.height)),
                                                 Image.Resampling.LANCZOS)

            # Resize image to fit in the right frame
            # Calculate the aspect ratio
            aspect_ratio = loaded_img.width / loaded_img.height

            if aspect_ratio >= 1:  # Width is greater than or equal to height
                if aspect_ratio >= RIGHT_FRAMES_WIDTH/TOP_FRAMES_HEIGHT:
                    right_img_resized_width = RIGHT_FRAMES_WIDTH
                    right_img_resized_height = int(RIGHT_FRAMES_WIDTH / aspect_ratio)

                else:
                    right_img_resized_height = TOP_FRAMES_HEIGHT
                    right_img_resized_width = int(TOP_FRAMES_HEIGHT * aspect_ratio)


            else:  # Height is greater than width
                right_img_resized_height = TOP_FRAMES_HEIGHT
                right_img_resized_width = int(TOP_FRAMES_HEIGHT * aspect_ratio)


            right_img_resized = loaded_img.resize((right_img_resized_width, right_img_resized_height),
                                                  Image.Resampling.LANCZOS)

            # Store the loaded images
            self.images.append({"image": right_img_resized,
                                "resized_image": left_img_resized,
                                "image_name": image_name,
                                "image_size": (loaded_img.width, loaded_img.height)})


        #Display the images loaded
        self.filter_and_display_images()




if __name__ == "__main__":
    root = customtkinter.CTk()
    app = ImageApp(root)
    root.mainloop()
