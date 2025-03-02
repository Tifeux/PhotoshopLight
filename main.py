import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
from PIL import Image, ImageDraw, ImageTk
import numpy as np

class ModernPhotoshop:
    def __init__(self, root):
        self.root = root
        self.root.title("Photoshop Light")
        self.root.geometry("1000x700")
        self.root.minsize(400, 300)
        
        # Variables
        self.drawing = False
        self.selecting = False
        self.magic_wand_active = False
        self.last_x = 0
        self.last_y = 0
        self.current_color = "black"
        self.brush_size = 5
        self.selection_rect = None
        self.selection_coords = None
        
        # Style 
        style = ttk.Style()
        style.configure("Toolbutton.TButton", font=("Arial", 10), padding=5)
        style.configure("TFrame", background="#f0f0f0")
        
        # Frame principal
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barre d'outils verticale à gauche
        self.toolbar = ttk.Frame(main_frame, width=70, relief=tk.RAISED)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Canvas redimensionnable
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Image PIL
        self.image = Image.new("RGB", (800, 600), "white")
        self.draw = ImageDraw.Draw(self.image)
        
        # Outils
        tools = [
            ("✏️", "Pinceau", self.use_brush),
            ("□", "Sélection", self.use_rect_select),
            ("✨", "Baguette", self.use_magic_wand),
            ("🗑️", "Effacer", self.erase_selection),
            ("🎨", "Couleur", self.choose_color),
            ("🧹", "Tout effacer", self.clear_canvas),
            ("💾", "Sauvegarder", self.save_image)
        ]
        for icon, text, cmd in tools:
            btn = ttk.Button(self.toolbar, text=f"{icon}\n{text}", command=cmd, style="Toolbutton.TButton")
            btn.pack(fill=tk.X, pady=2)
        
        # Slider pour la taille du pinceau
        ttk.Label(self.toolbar, text="Taille").pack(pady=5)
        self.size_slider = ttk.Scale(self.toolbar, from_=1, to=20, orient=tk.VERTICAL, 
                                   command=self.change_brush_size, length=100)
        self.size_slider.set(5)
        self.size_slider.pack(pady=5)
        
        # Bind des événements
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Configure>", self.resize_canvas)
        
    def resize_canvas(self, event):
        new_width, new_height = event.width, event.height
        self.image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.draw = ImageDraw.Draw(self.image)
        self.update_canvas()

    def update_canvas(self):
        self.canvas.delete("all")
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def use_brush(self):
        self.selecting = False
        self.magic_wand_active = False
        self.clear_selection()

    def use_rect_select(self):
        self.selecting = True
        self.magic_wand_active = False
        self.clear_selection()

    def use_magic_wand(self):
        self.selecting = False
        self.magic_wand_active = True
        self.clear_selection()

    def on_mouse_down(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.drawing = True

    def on_mouse_move(self, event):
        if self.drawing:
            if self.selecting:
                self.draw_selection(event.x, event.y)
            elif self.magic_wand_active:
                pass  # La baguette agit au relâchement
            else:
                self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                      width=self.brush_size, fill=self.current_color,
                                      capstyle=tk.ROUND, smooth=tk.TRUE)
                self.draw.line([(self.last_x, self.last_y), (event.x, event.y)], 
                              fill=self.current_color, width=self.brush_size)
            self.last_x, self.last_y = event.x, event.y

    def on_mouse_up(self, event):
        self.drawing = False
        if self.selecting:
            self.selection_coords = (min(self.last_x, event.x), min(self.last_y, event.y),
                                   max(self.last_x, event.x), max(self.last_y, event.y))
            self.draw_selection(self.selection_coords[0], self.selection_coords[1])
        elif self.magic_wand_active:
            print(f"Magic wand clicked at: ({self.last_x}, {self.last_y})")  # Debug
            self.magic_wand_select(self.last_x, self.last_y)

    def draw_selection(self, x, y):
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        self.selection_rect = self.canvas.create_rectangle(self.last_x, self.last_y, x, y, 
                                                         outline="#00f", dash=(4, 4), width=2)

    def magic_wand_select(self, x, y):
        self.clear_selection()
        pixels = np.array(self.image)
        if not (0 <= y < pixels.shape[0] and 0 <= x < pixels.shape[1]):
            print("Click outside canvas!")  # Debug
            return
        target_color = pixels[y, x]
        mask = self.flood_fill(pixels, x, y, target_color, tolerance=30)
        ys, xs = np.where(mask)
        if len(xs) > 0 and len(ys) > 0:
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            self.selection_coords = (x_min, y_min, x_max, y_max)
            self.selection_rect = self.canvas.create_rectangle(x_min, y_min, x_max, y_max,
                                                             outline="#00f", dash=(4, 4), width=2)
        else:
            print("No area selected by magic wand!")  # Debug

    def flood_fill(self, pixels, start_x, start_y, target_color, tolerance):
        height, width = pixels.shape[:2]
        mask = np.zeros((height, width), dtype=bool)
        target_color = tuple(map(int, target_color))  # Convertir en entiers
        to_check = [(start_x, start_y)]
        
        while to_check:
            x, y = to_check.pop()
            if not (0 <= x < width and 0 <= y < height) or mask[y, x]:
                continue
            current_color = tuple(map(int, pixels[y, x]))  # Convertir en entiers
            if self.color_distance(current_color, target_color) <= tolerance:
                mask[y, x] = True
                to_check.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
        return mask

    def color_distance(self, c1, c2):
        # Éviter les overflows en utilisant des entiers et en normalisant
        return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

    def erase_selection(self):
        if self.selection_coords:
            x1, y1, x2, y2 = self.selection_coords
            self.draw.rectangle([x1, y1, x2, y2], fill="white")
            self.update_canvas()
            self.clear_selection()

    def clear_selection(self):
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
            self.selection_coords = None

    def choose_color(self):
        color = colorchooser.askcolor(title="Choisir une couleur")[1]
        if color:
            self.current_color = color

    def clear_canvas(self):
        self.image = Image.new("RGB", (self.canvas.winfo_width(), self.canvas.winfo_height()), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.update_canvas()
        self.clear_selection()

    def change_brush_size(self, value):
        self.brush_size = int(float(value))

    def save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                               filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image.save(file_path)

def main():
    root = tk.Tk()
    app = ModernPhotoshop(root)
    root.mainloop()

if __name__ == "__main__":
    main()
