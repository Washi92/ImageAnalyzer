import os
import tkinter as tk
from tkinter import filedialog
import customtkinter
from PIL import Image, ImageTk
import numpy as np
from scipy import interpolate
from scipy.spatial.distance import euclidean
import copy
import json
import concurrent.futures

#####################
# GLOBAL VARIABLES
#####################
LIST_IMG_SPACING = 10
RESIZE_IMG_WIDTH = 150
MAX_LANDMARK_NB = 3
SIZE_LANDMARK = 7
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
LEFT_FRAMES_WIDTH = 300
RIGHT_FRAMES_WIDTH = SCREEN_WIDTH - LEFT_FRAMES_WIDTH
TOP_FRAMES_HEIGHT = 600


class ImageApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Analyzer")
        customtkinter.set_appearance_mode("system")

        # Calculate the position to center the window
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        x_position = (screen_width - SCREEN_WIDTH) // 2
        y_position = (screen_height - SCREEN_HEIGHT) // 2
        self.master.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+{x_position}+{y_position}")

        self.master.resizable(False,False)

        ############################################## VARIABLES ##############################################
        # List to store loaded images
        self.images = []
        self.image_markers = {}
        self.images_and_markers = {}
        self.current_img_name =""

        # For positioning landmarks
        self.coordinates_marker = []
        self.landmarks = []

        # For drawing curved lines
        self.points = []
        self.c_points = []
        self.c_lines = []

        ############################################## FRAMES & CANVAS ##############################################
        # Create main frames to split the screen in left and right side sides
        left_frame = customtkinter.CTkFrame(master=self.master)
        left_frame.pack(side="left", anchor="nw")
        right_frame = customtkinter.CTkFrame(master=self.master)
        right_frame.pack(side="right")

        # Frames to display the loaded images
        self.left_up_frame = customtkinter.CTkFrame(master=left_frame)
        self.left_up_frame.pack(side="top", fill="y", expand=True, anchor="nw")
        self.left_down_frame = customtkinter.CTkFrame(master=left_frame, width=LEFT_FRAMES_WIDTH,
                                                 height=SCREEN_HEIGHT - TOP_FRAMES_HEIGHT)
        self.left_down_frame.pack(side="bottom", anchor="nw")
        # Associate a Scrollbar to the left_up_frame
        self.scrollbar = customtkinter.CTkScrollbar(self.left_up_frame, orientation="vertical")
        self.scrollbar.pack(side="right", fill="y")

        # Frames to analyze the image
        self.right_up_frame = customtkinter.CTkFrame(master=right_frame, width=SCREEN_WIDTH - LEFT_FRAMES_WIDTH,
                                                height=TOP_FRAMES_HEIGHT)
        self.right_up_frame.pack(side="top", anchor="nw")

        self.right_down_frame = customtkinter.CTkFrame(master=right_frame, border_color="blue",
                                                       width=SCREEN_WIDTH - LEFT_FRAMES_WIDTH,
                                                       height=SCREEN_HEIGHT - TOP_FRAMES_HEIGHT)
        self.right_down_frame.pack(side="bottom", anchor="nw")

        # Canvas for displaying the loaded images and configure the scrollbar
        self.canvas_left = customtkinter.CTkCanvas(self.left_up_frame, width=LEFT_FRAMES_WIDTH,
                                                   height=TOP_FRAMES_HEIGHT, background="dark gray")
        self.canvas_left.pack()
        self.canvas_left.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.canvas_left.yview)

        # Canvas for displaying the selected image to analyze
        self.canvas_right = tk.Canvas(self.right_up_frame, background="dark gray",
                                                    width=SCREEN_WIDTH - LEFT_FRAMES_WIDTH,
                                                    height=TOP_FRAMES_HEIGHT)  # bd=0, highlightthickness=0
        self.canvas_right.pack()

        ############################################## TEXT INPUT ##############################################
        self.search_entry = customtkinter.CTkEntry(self.left_down_frame, placeholder_text="Search image", width=250)
        self.search_entry.place(relx=0.5, rely=0.25, anchor="center")
        self.search_entry.bind("<KeyRelease>", self.filtered_images)


        ############################################## BUTTONS ##############################################
        load_btn = customtkinter.CTkButton(master=self.left_down_frame, text="LOAD IMAGE", command=self.load_images)
        load_btn.place(relx=0.5, rely=0.6, anchor="center")

        self.create_marker_btn = customtkinter.CTkButton(master=self.right_down_frame, text="CREATE MARKER", state="disabled",
                                             text_color="white",command=self.create_marker)
        self.create_marker_btn.place(relx=0.3, rely=0.6, anchor="center")

        self.remove_marker_btn = customtkinter.CTkButton(master=self.right_down_frame, text="REMOVE MARKER",
                                                    state="disabled",
                                                    text_color="white", command=self.remove_marker)
        self.remove_marker_btn.place(relx=0.3, rely=0.8, anchor="center")

        self.draw_btn = customtkinter.CTkButton(master=self.right_down_frame, text="DRAW", state="disabled",
                                            text_color="white", width=100, command=self.draw_curve)
        self.draw_btn.place(relx=0.47, rely=0.6, anchor="center")


        self.export_btn = customtkinter.CTkButton(master=self.right_down_frame, text="EXPORT", state="disabled",
                                             text_color="white", width=110, height=50,
                                             command=self.export_images_to_json)
        self.export_btn.place(relx=0.1, rely=0.37, anchor="center")

        self.save_btn = customtkinter.CTkButton(master=self.right_down_frame, text="SAVE", state="disabled",
                                            text_color="white", width=110, height=50, command=self.save_position_markers)
        self.save_btn.place(relx=0.1, rely=0.74, anchor="center")


        ############################################## SWITCHES ##############################################
        self.position_marker_switch_var = customtkinter.StringVar(value="off")
        self.position_marker_switch = customtkinter.CTkSwitch(master=self.right_down_frame, text="Place Markers",
                                                              text_color="white", variable=self.position_marker_switch_var,
                                                              onvalue="on", offvalue="off", command=self.position_marker_switcher,
                                                              state="disabled")
        self.position_marker_switch.place(relx=0.3, rely=0.3, anchor="center")

        self.draw_curve_switch_var = customtkinter.StringVar(value="off")
        self.draw_curve_switch = customtkinter.CTkSwitch(master=self.right_down_frame, text="Draw Curve", text_color="white",
                                                         variable=self.draw_curve_switch_var, onvalue="on", offvalue="off",
                                                         command=self.draw_curve_switcher, state="disabled")
        self.draw_curve_switch.place(relx=0.47, rely=0.3, anchor="center")



        ############################################## SLIDERS ##############################################
        #Slider for length/pixel
        self.length_pixel_ratio = customtkinter.IntVar(value=10)
        slider_lp = customtkinter.CTkSlider(master=self.right_down_frame, from_=1, to=10, width=100,
                                             variable=self.length_pixel_ratio)
        slider_lp.place(relx=0.75, rely=0.3, anchor="center")

        # Slider to choose the resolution or the curved lines
        self.curve_resolution = customtkinter.IntVar(value=50)
        slider_cl = customtkinter.CTkSlider(master=self.right_down_frame, from_=4, to=100, width=100,
                                            variable=self.curve_resolution)
        slider_cl.place(relx=0.75, rely=0.6, anchor="center")


        ############################################## LABELS ##############################################
        self.perimeter_lb = customtkinter.CTkLabel(master=self.right_down_frame, text="", fg_color=("transparent"))
        self.perimeter_lb.place(relx=0.6, rely=0.3, anchor="center",)
        self.area_lb = customtkinter.CTkLabel(master=self.right_down_frame, text="", fg_color=("transparent"))
        self.area_lb.place(relx=0.6, rely=0.5, anchor="center")

        self.lenpix_lb = customtkinter.CTkLabel(master=self.right_down_frame, textvariable=self.length_pixel_ratio)
        self.lenpix_lb.place(relx=0.81, rely=0.3, anchor="center")

        self.scale_lb = customtkinter.CTkLabel(master=self.right_down_frame, text="mm/pixel" )
        self.scale_lb.place(relx=0.85, rely=0.3, anchor="center")

        self.c_resolution_lb = customtkinter.CTkLabel(master=self.right_down_frame, textvariable=self.curve_resolution)
        self.c_resolution_lb.place(relx=0.81, rely=0.6, anchor="center")
        self.scale_lb = customtkinter.CTkLabel(master=self.right_down_frame, text="spline resolution")
        self.scale_lb.place(relx=0.87, rely=0.6, anchor="center")


    ############################################## FUNCTIONS ##############################################
    def position_marker_switcher(self):
        if self.position_marker_switch_var.get() == "on":
            # Disable other functionalitites
            self.draw_curve_switch.configure(state="disabled")
            self.draw_btn.configure(state="disabled")

            # Activate marker functionalitites
            self.position_marker_switch.configure(state="normal")
            self.export_btn.configure(state="normal")
            self.create_marker_btn.configure(state="normal")
            self.remove_marker_btn.configure(state="normal")
            self.save_btn.configure(state="normal")

        else:
            # Remove the points from the canvas
            self.points.clear()
            for p in self.c_points:
                self.canvas_right.delete(p)
            self.c_points = []

            # Activate other functionalitites
            self.draw_curve_switch.configure(state="normal")
            self.create_marker_btn.configure(state="disabled")
            self.remove_marker_btn.configure(state="disabled")

    def draw_curve_switcher(self):
        if self.draw_curve_switch_var.get() == "on":
            # Disable other functionalitites
            self.create_marker_btn.configure(state="disabled")
            self.remove_marker_btn.configure(state="disabled")
            # export_btn.configure(state="disabled")

            self.position_marker_switch_var.set("off")
            self.position_marker_switch.configure(state="disabled")

            # Activate curve functionalitites
            self.draw_curve_switch.configure(state="normal")
            self.draw_btn.configure(state="normal")
            self.canvas_right.bind("<Button-1>", self.draw_point)

        else:
            self.draw_btn.configure(state="disabled")
            self.canvas_right.unbind("<Button-1>")
            # Remove labels form the canvas
            self.perimeter_lb.configure(text='')
            self.area_lb.configure(text='')

            # Remove the points from the canvas
            for p in self.c_points:
                self.canvas_right.delete(p)
            self.c_points = []

            # Clear points before drawing new curved lines
            self.points.clear()

            # Remove the curved lines from the canvas
            for l in self.c_lines:
                self.canvas_right.delete(l)
            self.c_lines = []

            # Activate other functionalitites
            self.position_marker_switch.configure(state="normal")

    def save_position_markers(self):
        print(f"\nDICTIONARY current_img_name: {self.current_img_name}")
        #Avoid assigning the reference
        self.images_and_markers[self.current_img_name] = copy.deepcopy(self.image_markers)
        print(self.images_and_markers)

    def export_images_to_json(self, filename="images.json"):
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
        # Skip if there are already 3 markers
        if len(self.landmarks) >= MAX_LANDMARK_NB:
            return
        marker_id = int(len(self.landmarks))

        # Position the marker in the center of the image
        x1,y1 = (RIGHT_FRAMES_WIDTH/2) - SIZE_LANDMARK, (TOP_FRAMES_HEIGHT/2) - SIZE_LANDMARK
        x2, y2 = x1+SIZE_LANDMARK, y1+SIZE_LANDMARK
        marker = self.canvas_right.create_oval(x1, y1, x1 + 20, y1 + 20, fill="blue", tags=f"marker{marker_id}")

        self.landmarks.append(marker)

        #Bind motion to each new marker
        self.canvas_right.tag_bind(f"marker{marker_id}", "<B1-Motion>",
                                   lambda e, m=marker_id: self.move_marker(e, m))
        self.canvas_right.tag_bind(f"marker{marker_id}", "<ButtonRelease-1>",
                                   lambda e, m=marker_id: self.move_marker(e, m))

    def move_marker(self, event, marker_id):
        if self.position_marker_switch_var.get() == "off":
            return
        # Move the marker with the mouse
        self.canvas_right.coords(self.landmarks[marker_id],
                                 event.x - SIZE_LANDMARK,
                                 event.y - SIZE_LANDMARK,
                                 event.x + SIZE_LANDMARK,
                                 event.y + SIZE_LANDMARK)

        # Save the center coordinates of each marker
        x1, y1, x2, y2 = self.canvas_right.coords(self.landmarks[marker_id])
        coord_x = (x1+x2)/2
        coord_y = (y1+y2)/2
        self.coordinates_marker.append((coord_x,coord_y))

        # Append only the last position of the marker
        self.image_markers[marker_id] = self.coordinates_marker[-1]

    def remove_marker(self):
        #Remove last marker positioned from all lists
        if self.landmarks:
            last_marker = self.landmarks.pop()
            self.canvas_right.delete(last_marker)
            self.coordinates_marker.pop()
        # Remove last marker positioned from dictionary
        if self.image_markers:
            del self.image_markers[next(reversed(self.image_markers))]

    def draw_point(self, event):
        # Retrieve the coordinates from the clicked area and save it in points[]
        x, y = event.x, event.y
        self.points.append((x, y))
        size_point = SIZE_LANDMARK/2
        x1, y1 = (event.x - size_point), (event.y - size_point)
        x2, y2 = (event.x + size_point), (event.y + size_point)

        # Draw points for each click and save it in c_points
        point = self.canvas_right.create_oval(x1, y1, x2, y2, fill="red", outline='')
        self.c_points.append(point)

    def draw_curve(self):
        if not self.points:
            return
        #Clean variables
        perimeter = 0
        area = 0

        x = np.array([point[0] for point in self.points])
        y = np.array([point[1] for point in self.points])

        # append the starting x,y coordinates
        x = np.r_[x, x[0]]
        y = np.r_[y, y[0]]

        # Interpolate x,y. force the spline fit to pass through all the input points (s=0)
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

        # Convert the results according to the mm/pixel ration
        factor = self.length_pixel_ratio.get()
        perimeter = perimeter / factor
        area = area / int(factor ** 2)
        # Update the corresponding labels
        self.perimeter_lb.configure(text=f'Perimeter: {perimeter:.2f}')
        self.area_lb.configure(text=f'Area: {area:.2f}')

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
                image_label = tk.Label(self.canvas_left, image=tk_image)
                image_label.image = tk_image  # Keep a reference to avoid garbage collection

                # Create a button associated with the current image & display it
                btn_img = tk.Button(self.canvas_left, text=None, image= tk_image,
                                   command=lambda i=i: self.display_main_image(i))

                self.canvas_left.create_window(LIST_IMG_SPACING, y_position, anchor=tk.NW, window=btn_img)

                # Display image info to the right of the image
                info_text = f"Name: {img["image_name"]}\nDimensions: {img["image_size"][0]}x{img["image_size"][1]}"
                info_label = tk.Label(self.canvas_left, text=info_text, anchor=tk.W, justify=tk.LEFT)
                self.canvas_left.create_window(LIST_IMG_SPACING + RESIZE_IMG_WIDTH + LIST_IMG_SPACING,
                                               y_position, anchor=tk.NW, width=210, window=info_label)

                y_position += resized_image.height + LIST_IMG_SPACING

        # Update the canvas to fit with the scrollbar
        self.canvas_left.config(scrollregion=self.canvas_left.bbox(tk.ALL))

    def display_main_image(self, image_index):
        self.current_img_name = self.images[image_index]["image_name"]
        # Clean variables and canvas
        self.canvas_right.delete("all")
        self.points.clear()
        self.landmarks.clear()
        self.image_markers.clear()
        self.perimeter_lb.configure(text='')
        self.area_lb.configure(text='')

        # Load selected image
        image_tk = ImageTk.PhotoImage(self.images[image_index]["image"])
        self.canvas_right.image = image_tk

        # Display the image in the center
        x = (RIGHT_FRAMES_WIDTH - image_tk.width()) / 2
        y = (TOP_FRAMES_HEIGHT - image_tk.height()) / 2
        self.canvas_right.create_image(x, y, image=image_tk, anchor="nw")

        # Retrieve and display existing larkers
        if bool(self.images_and_markers.get(self.current_img_name, {})):
            self.display_markers(self.current_img_name)

        self.draw_curve_switch.configure(state="normal")
        self.position_marker_switch.configure(state="normal")

    def display_markers(self, img_name):
        #Retrieve existing markers for a specific image
        self.image_markers = self.images_and_markers[img_name]

        nb_markers = len(self.images_and_markers[img_name])
        # Retrieve coordinates for each marker and bind motion
        for i in range(nb_markers):
            x, y = self.images_and_markers[img_name][i]
            x1, y1 = x-SIZE_LANDMARK, y-SIZE_LANDMARK
            x2, y2 = x+SIZE_LANDMARK, y+SIZE_LANDMARK

            marker = self.canvas_right.create_oval(x1, y1, x2, y2, fill="blue", tags=f"marker{i}")
            self.landmarks.append(marker)
            # Bind motion to specific marker
            self.canvas_right.tag_bind(f"marker{i}", "<B1-Motion>",
                lambda e, m=i: self.move_marker(e, m))
            self.canvas_right.tag_bind(f"marker{i}", "<ButtonRelease-1>",
              lambda e, m=i: self.move_marker(e, m))

        # Save the current position of markers
        self.save_position_markers()

    def process_load_image(self, file_path):
        image_name = os.path.basename(file_path)
        # Avoid loading images with the same name
        if any(img["image_name"] == image_name for img in self.images):
            return None

        loaded_img = Image.open(file_path)

        # Resize image to fit in the left frame
        left_img_resized = loaded_img.resize((RESIZE_IMG_WIDTH,
                                              int((RESIZE_IMG_WIDTH / loaded_img.width) * loaded_img.height)),
                                             Image.Resampling.LANCZOS)

        # Resize image to fit in the right frame
        # Calculate the aspect ratio
        aspect_ratio = loaded_img.width / loaded_img.height

        if aspect_ratio >= 1:  # Width is greater than or equal to height
            if aspect_ratio >= RIGHT_FRAMES_WIDTH / TOP_FRAMES_HEIGHT:
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

    def load_images(self):
        # Clear the text in the entry
        self.search_entry.delete(0, tk.END)

        # Open a file dialog to select images
        file_paths = filedialog.askopenfilenames(title="Select Images",
                                                 filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        #Use Multi-Threading for reading the images
        num_cores = os.cpu_count() or 1
        # Split the list of paths into chunks
        chunk_size = max(len(file_paths) // num_cores, 1)
        chunks = [file_paths[i:i + chunk_size] for i in range(0, len(file_paths), chunk_size)]
        chunks = [item for sublist in chunks for item in sublist]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Process each chunk in a separate thread
            results = list(executor.map(self.process_load_image, chunks))

        # Display the images loaded
        self.filter_and_display_images()


if __name__ == "__main__":
    root = customtkinter.CTk()
    app = ImageApp(root)
    root.mainloop()