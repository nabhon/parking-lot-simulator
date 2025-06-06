import cv2
import threading
from tkinter import *
from PIL import Image, ImageTk
from detector import detect_plate_and_read
from database import handle_entry_detection, handle_exit_detection

class App:
    def __init__(self):
        self.window = Tk()
        self.window.title("Nabhon License Plate Reader")
        self.window.geometry("800x600")

        # Video capture
        self.cap = cv2.VideoCapture(0)

        # GUI elements
        self.label = Label(self.window)
        self.label.pack()

        self.text_var = StringVar()
        self.text_var.set("Mode: Entrance")
        self.text_display = Label(self.window, textvariable=self.text_var, font=("Arial", 14))
        self.text_display.pack()

        self.mode = StringVar(value="Entrance")  # Mode state
        self.mode_label = Label(self.window, text="Select Mode:", font=("Arial", 12))
        self.mode_label.pack()

        self.mode_menu = OptionMenu(self.window, self.mode, "Entrance", "Exit")
        self.mode_menu.pack()

        self.window.bind("<m>", self.toggle_mode)  # M key toggles mode
        self.window.bind("<q>", self.quit_app)  # Q key exits program

        self.running = True
        self.thread = threading.Thread(target=self.update)
        self.thread.start()

    def quit_app(self, event=None):
        self.running = False
        self.cap.release()
        self.window.quit()
        self.window.destroy()

    def toggle_mode(self, event=None):
        # Toggle between Entrance and Exit mode
        new_mode = "Exit" if self.mode.get() == "Entrance" else "Entrance"
        self.mode.set(new_mode)
        self.text_var.set(f"🔁 Switched to {new_mode} Mode")

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Resize frame for GUI
            frame_resized = cv2.resize(frame, (640, 480))
            img = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            img_tk = ImageTk.PhotoImage(image=img_pil)

            # Display in GUI
            self.label.imgtk = img_tk
            self.label.configure(image=img_tk)

            # Detect plate
            plate, conf = detect_plate_and_read(frame_resized)
            if plate and conf > 0.5:
                current_mode = self.mode.get()

                if current_mode == "Entrance":
                    result, _ = handle_entry_detection(plate)
                    if result == "entry":
                        self.text_var.set(f"🟢 Entry: {plate} | Confidence: {conf:.2f}")
                    elif result == "already_inside":
                        self.text_var.set(f"⚠️ Already inside: {plate}")
                elif current_mode == "Exit":
                    result, fee = handle_exit_detection(plate)
                    if result == "exit":
                        self.text_var.set(f"🔴 Exit: {plate} | Fee ฿{fee:.2f} | Confidence: {conf:.2f}")
                    elif result == "not_found":
                        self.text_var.set(f"⚠️ Not found: {plate}")

            self.window.update_idletasks()
            self.window.update()

    def run(self):
        self.window.mainloop()
        self.running = False
        self.cap.release()
