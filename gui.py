import cv2
import threading
from tkinter import *
from PIL import Image, ImageTk
from detector import detect_plate_and_read
from database import handle_entry_detection, handle_exit_detection
import time
from datetime import datetime

class App:
    def __init__(self):
        self.window = Tk()
        self.window.title("Nabhon License Plate Reader")
        self.window.geometry("800x600")

        # Video capture
        self.cap = cv2.VideoCapture(0)

        # Create main container
        self.main_container = Frame(self.window)
        self.main_container.pack(fill=BOTH, expand=True)

        # Create scan view
        self.scan_view = Frame(self.main_container)
        self.label = Label(self.scan_view)
        self.label.pack()

        self.text_var = StringVar()
        self.text_var.set("Mode: Entrance")
        self.text_display = Label(self.scan_view, textvariable=self.text_var, font=("Arial", 14))
        self.text_display.pack()

        self.mode = StringVar(value="Entrance")  # Mode state
        self.mode_label = Label(self.scan_view, text="Select Mode:", font=("Arial", 12))
        self.mode_label.pack()

        self.mode_menu = OptionMenu(self.scan_view, self.mode, "Entrance", "Exit")
        self.mode_menu.pack()

        # Create entry view
        self.entry_view = Frame(self.main_container)
        self.entry_view.pack_propagate(False)  # Prevent frame from shrinking
        
        # Center container for entry information
        self.entry_center = Frame(self.entry_view)
        self.entry_center.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        self.entry_title = Label(self.entry_center, text="ยินดีตอนรับ", font=("Arial", 24, "bold"))
        self.entry_title.pack(pady=20)
        
        self.plate_var = StringVar()
        self.plate_display = Label(self.entry_center, textvariable=self.plate_var, font=("Arial", 20))
        self.plate_display.pack(pady=10)
        
        self.time_var = StringVar()
        self.time_display = Label(self.entry_center, textvariable=self.time_var, font=("Arial", 18))
        self.time_display.pack(pady=10)

        # Create exit view
        self.exit_view = Frame(self.main_container)
        self.exit_view.pack_propagate(False)
        
        # Center container for exit information
        self.exit_center = Frame(self.exit_view)
        self.exit_center.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        self.qr_label = Label(self.exit_center)
        self.qr_label.pack(pady=20)
        
        self.exit_plate_var = StringVar()
        self.exit_plate_display = Label(self.exit_center, textvariable=self.exit_plate_var, font=("Arial", 20))
        self.exit_plate_display.pack(pady=10)
        
        self.exit_time_var = StringVar()
        self.exit_time_display = Label(self.exit_center, textvariable=self.exit_time_var, font=("Arial", 18))
        self.exit_time_display.pack(pady=10)
        
        self.exit_fee_var = StringVar()
        self.exit_fee_display = Label(self.exit_center, textvariable=self.exit_fee_var, font=("Arial", 18))
        self.exit_fee_display.pack(pady=10)

        self.window.bind("<m>", self.toggle_mode)  # M key toggles mode
        self.window.bind("<q>", self.quit_app)  # Q key exits program
        self.window.bind("<g>", self.return_to_scan)  # G key returns to scan view

        self.running = True
        self.showing_entry = False
        self.showing_exit = False
        self.entry_end_time = 0
        self.thread = threading.Thread(target=self.update)
        self.thread.start()

        # Show scan view initially
        self.show_scan_view()

    def show_scan_view(self):
        self.entry_view.pack_forget()
        self.exit_view.pack_forget()
        self.scan_view.pack(fill=BOTH, expand=True)

    def show_entry_view(self):
        self.scan_view.pack_forget()
        self.exit_view.pack_forget()
        self.entry_view.pack(fill=BOTH, expand=True)
        # Ensure the entry view takes full window size
        self.entry_view.configure(width=800, height=600)

    def show_exit_view(self):
        self.scan_view.pack_forget()
        self.entry_view.pack_forget()
        self.exit_view.pack(fill=BOTH, expand=True)
        self.exit_view.configure(width=800, height=600)

    def quit_app(self, event=None):
        self.running = False
        self.cap.release()
        self.window.quit()
        self.window.destroy()

    def toggle_mode(self, event=None):
        # Toggle between Entrance and Exit mode
        new_mode = "Exit" if self.mode.get() == "Entrance" else "Entrance"
        self.mode.set(new_mode)
        self.text_var.set(f"Mode: {new_mode}")
        # Always show scan view when switching modes
        self.show_scan_view()

    def return_to_scan(self, event=None):
        if self.showing_exit:
            self.showing_exit = False
            self.show_scan_view()
            self.text_var.set(f"Mode: {self.mode.get()}")

    def show_entry_info(self, plate):
        self.showing_entry = True
        self.entry_end_time = time.time() + 5  # Show for 5 seconds
        
        # Update entry view information
        self.plate_var.set(f"เลขทะเบียน : {plate}")
        self.time_var.set(f"เวลาเข้า : {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Switch to entry view
        self.show_entry_view()

    def show_exit_info(self, plate, entry_time, fee):
        self.showing_exit = True
        
        # Load and display QR code
        try:
            qr_image = Image.open("qr.png")
            qr_image = qr_image.resize((200, 200), Image.Resampling.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_image)
            self.qr_label.configure(image=qr_photo)
            self.qr_label.image = qr_photo
        except Exception as e:
            print(f"Error loading QR code: {e}")
        
        # Calculate parking duration
        entry_datetime = datetime.fromisoformat(entry_time)
        current_datetime = datetime.now()
        duration = current_datetime - entry_datetime
        
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        # Update exit view information
        self.exit_plate_var.set(f"เลขทะเบียน : {plate}")
        self.exit_time_var.set(f"เวลาจอด : {hours} ชั่วโมง {minutes} นาที")
        self.exit_fee_var.set(f"ราคา : ฿{fee:.2f}")
        
        # Switch to exit view
        self.show_exit_view()

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

            # Check if we should return to scanning mode
            if self.showing_entry and time.time() > self.entry_end_time:
                self.showing_entry = False
                self.show_scan_view()
                self.text_var.set(f"Mode: {self.mode.get()}")

            # Only detect if not showing entry/exit info
            if not self.showing_entry and not self.showing_exit:
                # Detect plate
                plate, conf = detect_plate_and_read(frame_resized)
                if plate and conf > 0.5:
                    current_mode = self.mode.get()

                    if current_mode == "Entrance":
                        result, _ = handle_entry_detection(plate)
                        if result == "entry":
                            self.show_entry_info(plate)
                        elif result == "already_inside":
                            self.text_var.set(f"⚠️ Already inside: {plate}")
                    elif current_mode == "Exit":
                        result, fee = handle_exit_detection(plate)
                        if result == "exit":
                            # Get the entry time from the database
                            from database import db, plates, Plate
                            record = plates.get((Plate.plate_number == plate) & (Plate.exit_time != None))
                            if record:
                                entry_time = record["entry_time"]
                                self.show_exit_info(plate, entry_time, fee)
                        elif result == "not_found":
                            self.text_var.set(f"⚠️ Not found: {plate}")

            self.window.update_idletasks()
            self.window.update()

    def run(self):
        self.window.mainloop()
        self.running = False
        self.cap.release()
