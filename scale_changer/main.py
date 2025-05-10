import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import os
import math

ASPECTS = {
    "16:9 (HD/Widescreen)": (16, 9),
    "4:3 (Standard)": (4, 3),
    "21:9 (Cinema)": (21, 9),
    "1:1 (Square)": (1, 1),
    "9:16 (Vertical)": (9, 16)
}

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def detect_resolution_and_aspect(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, None, None
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    divisor = gcd(width, height)
    aspect_simple = f"{width//divisor}:{height//divisor}"
    return width, height, aspect_simple

def get_new_resolution(width, height, new_aspect):
    # Keep the same width, adjust height to match new aspect
    new_w, new_h = new_aspect
    new_height = int(width * new_h / new_w)
    return width, new_height

def scale_video(input_path, output_path, new_aspect, use_gpu=False):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return False, "Could not open input video."

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    new_width, new_height = get_new_resolution(width, height, new_aspect)

    # Output video writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Use GPU if available and requested
        if use_gpu and cv2.cuda.getCudaEnabledDeviceCount() > 0:
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            resized_gpu = cv2.cuda.resize(gpu_frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            frame_resized = resized_gpu.download()
        else:
            frame_resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        out.write(frame_resized)

    cap.release()
    out.release()
    return True, "Scaling completed successfully."

class ScaleChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ScaleChanger")
        self.input_path = ""
        self.output_path = ""
        self.current_aspect = tk.StringVar()
        self.new_aspect = tk.StringVar(value=list(ASPECTS.keys())[0])

        # Input file
        tk.Label(root, text="Input Video:").grid(row=0, column=0, sticky="e")
        self.input_entry = tk.Entry(root, width=40, state="readonly")
        self.input_entry.grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.browse_input).grid(row=0, column=2)

        # Output file
        tk.Label(root, text="Output Video:").grid(row=1, column=0, sticky="e")
        self.output_entry = tk.Entry(root, width=40, state="readonly")
        self.output_entry.grid(row=1, column=1)
        tk.Button(root, text="Browse", command=self.browse_output).grid(row=1, column=2)

        # Current aspect
        tk.Label(root, text="Current Aspect Ratio:").grid(row=2, column=0, sticky="e")
        self.current_aspect_label = tk.Label(root, textvariable=self.current_aspect, width=20, relief="sunken")
        self.current_aspect_label.grid(row=2, column=1, sticky="w")

        # New aspect
        tk.Label(root, text="New Aspect Ratio:").grid(row=3, column=0, sticky="e")
        self.aspect_menu = ttk.Combobox(root, textvariable=self.new_aspect, values=list(ASPECTS.keys()), state="readonly")
        self.aspect_menu.grid(row=3, column=1, sticky="w")

        # Start button
        self.start_btn = tk.Button(root, text="Start Scaling", command=self.start_scaling)
        self.start_btn.grid(row=4, column=1, pady=10)

    def browse_input(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if path:
            self.input_path = path
            self.input_entry.config(state="normal")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)
            self.input_entry.config(state="readonly")
            width, height, aspect = detect_resolution_and_aspect(path)
            if aspect:
                self.current_aspect.set(f"{width}x{height} ({aspect})")
            else:
                self.current_aspect.set("Unknown")

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Output Video As",
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4"), ("AVI Video", "*.avi"), ("All Files", "*.*")]
        )
        if path:
            self.output_path = path
            self.output_entry.config(state="normal")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)
            self.output_entry.config(state="readonly")

    def start_scaling(self):
        if not self.input_path or not self.output_path:
            messagebox.showerror("Error", "Please select both input and output files.")
            return
        aspect_key = self.new_aspect.get()
        if aspect_key not in ASPECTS:
            messagebox.showerror("Error", "Please select a valid new aspect ratio.")
            return
        use_gpu = cv2.cuda.getCudaEnabledDeviceCount() > 0
        success, msg = scale_video(self.input_path, self.output_path, ASPECTS[aspect_key], use_gpu)
        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScaleChangerApp(root)
    root.mainloop()