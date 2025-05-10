import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import os
import math

# Set the environment variable to prioritize FFMPEG over Media Foundation
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

ASPECTS = {
    "16:9 (HD/Widescreen)": (16, 9),
    "4:3 (Standard)": (4, 3),
    "21:9 (Cinema)": (21, 9),
    "1:1 (Square)": (1, 1),
    "9:16 (Vertical)": (9, 16)
}

PREDEFINED_RESOLUTIONS = {
    "16:9 - 1920x1080 (Full HD)": (1920, 1080),
    "16:9 - 1280x720 (HD)": (1280, 720),
    "16:9 - 2560x1440 (QHD)": (2560, 1440),
    "16:9 - 3840x2160 (4K UHD)": (3840, 2160),
    "4:3 - 1024x768 (XGA)": (1024, 768),
    "4:3 - 800x600 (SVGA)": (800, 600),
    "1:1 - 1080x1080 (Square)": (1080, 1080),
    "9:16 - 1080x1920 (Vertical)": (1080, 1920)
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

def scale_video(input_path, output_path, new_resolution, use_gpu=False, progress_callback=None):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return False, "Could not open input video."

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Dynamically select the codec based on the output file extension
    if output_path.endswith(".mp4"):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for .mp4 files
    else:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Use 'XVID' for other formats like .avi

    new_width, new_height = new_resolution

    # Output video writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))

    frame_count = 0
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

        # Update progress
        frame_count += 1
        if progress_callback:
            progress_callback(frame_count, total_frames)

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
        self.selected_resolution = tk.StringVar(value=list(PREDEFINED_RESOLUTIONS.keys())[0])

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

        # Resolution dropdown
        tk.Label(root, text="Select Resolution:").grid(row=3, column=0, sticky="e")
        self.resolution_menu = ttk.Combobox(root, textvariable=self.selected_resolution, values=list(PREDEFINED_RESOLUTIONS.keys()), state="readonly")
        self.resolution_menu.grid(row=3, column=1, sticky="w")

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, pady=10)

        # Start button
        self.start_btn = tk.Button(root, text="Start Scaling", command=self.start_scaling)
        self.start_btn.grid(row=5, column=1, pady=10)

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

        resolution_key = self.selected_resolution.get()
        if resolution_key not in PREDEFINED_RESOLUTIONS:
            messagebox.showerror("Error", "Please select a valid resolution.")
            return

        new_width, new_height = PREDEFINED_RESOLUTIONS[resolution_key]

        def update_progress(current, total):
            progress = int((current / total) * 100)
            self.progress["value"] = progress
            self.root.update_idletasks()

        use_gpu = cv2.cuda.getCudaEnabledDeviceCount() > 0
        success, msg = scale_video(self.input_path, self.output_path, (new_width, new_height), use_gpu, update_progress)
        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)
        self.progress["value"] = 0  # Reset progress bar

if __name__ == "__main__":
    root = tk.Tk()
    app = ScaleChangerApp(root)
    root.mainloop()