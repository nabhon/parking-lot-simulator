import cv2
import threading
from tkinter import *
from PIL import Image, ImageTk
from detector import detect_plate_and_read
from database import handle_entry_detection, handle_exit_detection, db, plates, Plate
import time
from datetime import datetime
import csv
import os

class App:
    def __init__(self):
        self.window = Tk()
        self.window.title("Nabhon License Plate Reader")
        self.window.geometry("800x600")

        # อ่านกล้อง
        self.cap = cv2.VideoCapture(0)

        # สร้าง container
        self.main_container = Frame(self.window)
        self.main_container.pack(fill=BOTH, expand=True)

        # สร้างหน้าจอสแกน
        self.scan_view = Frame(self.main_container)
        self.label = Label(self.scan_view)
        self.label.pack()

        self.text_var = StringVar()
        self.text_var.set("Mode: Entrance")
        self.text_display = Label(self.scan_view, textvariable=self.text_var, font=("Arial", 14))
        self.text_display.pack()

        self.mode = StringVar(value="Entrance")  # สถานะของโหมด

        # สร้างกรอบสำหรับปุ่ม export CSV
        self.export_frame = Frame(self.scan_view)
        self.export_frame.pack(side=BOTTOM, fill=X, padx=10, pady=10)
        
        # สร้างปุ่ม export CSV
        self.export_button = Button(self.export_frame, text="Export to CSV", command=self.export_to_csv, font=("Arial", 12), height=2)
        self.export_button.pack(side=RIGHT)

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

        # กด M Q G เพื่อเปลี่ยนโหมด
        self.window.bind("<m>", self.toggle_mode)
        self.window.bind("<q>", self.quit_app)
        self.window.bind("<g>", self.return_to_scan)

        self.running = True
        self.showing_entry = False
        self.showing_exit = False
        self.entry_end_time = 0
        self.thread = threading.Thread(target=self.update)
        self.thread.start()

        # แสดงหน้าจอสแกนเมื่อเริ่ม
        self.show_scan_view()

    def show_scan_view(self):
        self.entry_view.pack_forget()
        self.exit_view.pack_forget()
        self.scan_view.pack(fill=BOTH, expand=True)

    def show_entry_view(self):
        self.scan_view.pack_forget()
        self.exit_view.pack_forget()
        self.entry_view.pack(fill=BOTH, expand=True)
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
        # เปลี่ยนโหมด
        new_mode = "Exit" if self.mode.get() == "Entrance" else "Entrance"
        self.mode.set(new_mode)
        self.text_var.set(f"Mode: {new_mode}")
        # แสดงหน้าจอสแกนเสมอเมื่อเปลี่ยนโหมด
        self.show_scan_view()

    def return_to_scan(self, event=None):
        if self.showing_exit:
            self.showing_exit = False
            self.show_scan_view()
            self.text_var.set(f"Mode: {self.mode.get()}")

    def show_entry_info(self, plate):
        self.showing_entry = True
        self.entry_end_time = time.time() + 5  # แสดงผลการเข้า 5 วินาที
        
        # เก็บค่าข้อมูลหน้าจอการเข้า
        self.plate_var.set(f"เลขทะเบียน : {plate}")
        self.time_var.set(f"เวลาเข้า : {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # เปลี่ยนไปหน้าจอการเข้า
        self.show_entry_view()

    def show_exit_info(self, plate, entry_time, fee):
        self.showing_exit = True
        
        # แสดง QR code
        try:
            qr_image = Image.open("qr.png")
            qr_image = qr_image.resize((200, 200), Image.Resampling.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_image)
            self.qr_label.configure(image=qr_photo)
            self.qr_label.image = qr_photo
        except Exception as e:
            print(f"Error loading QR code: {e}")
        
        # คำนวณระยะเวลาการจอด
        entry_datetime = datetime.fromisoformat(entry_time)
        current_datetime = datetime.now()
        duration = current_datetime - entry_datetime
        
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        # เก็บค่าข้อมูลหน้าจอการออก
        self.exit_plate_var.set(f"เลขทะเบียน : {plate}")
        self.exit_time_var.set(f"เวลาจอด : {hours} ชั่วโมง {minutes} นาที")
        self.exit_fee_var.set(f"ราคา : ฿{fee:.2f}")
        
        # เปลี่ยนไปหน้าจอการออก
        self.show_exit_view()

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame_resized = cv2.resize(frame, (640, 480))
            img = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            img_tk = ImageTk.PhotoImage(image=img_pil)

            # แสดงภาพบนหน้าจอ
            self.label.imgtk = img_tk
            self.label.configure(image=img_tk)

            # ตรวจสอบว่าควรกลับไปหน้าจอสแกนจากการแสดงผล
            if self.showing_entry and time.time() > self.entry_end_time:
                self.showing_entry = False
                self.show_scan_view()
                self.text_var.set(f"Mode: {self.mode.get()}")

            # ตรวจว่าแสดงข้อมูลอยู่ไหม
            if not self.showing_entry and not self.showing_exit:
                # ตรวจสอบทะเบียนรถ
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
                            # ดึงข้อมูลเวลาเข้าจาก database
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

    def export_to_csv(self):
        # สร้างชื่อไฟล์ด้วยวันที่และเวลา
        filename = f"parking_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # ดึงข้อมูลทั้งหมดจากฐานข้อมูล
        all_records = plates.all()
        
        # เขียนลงไฟล์ CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['plate_number', 'entry_time', 'exit_time', 'fee']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in all_records:
                writer.writerow(record)
        
        self.text_var.set(f"Exported to {filename}")
        
        self.window.after(3000, lambda: self.text_var.set(f"Mode: {self.mode.get()}"))
