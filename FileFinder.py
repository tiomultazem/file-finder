import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, PhotoImage
import threading
import time
from datetime import datetime

def browse_src():
    src = filedialog.askdirectory()
    if src:
        entry_src.delete(0, tk.END)
        entry_src.insert(0, src)

def browse_dst():
    dst = filedialog.askdirectory()
    if dst:
        entry_dst.delete(0, tk.END)
        entry_dst.insert(0, dst)

def start_copy():
    threading.Thread(target=copy_files).start()

def update_button_label():
    mode = operation_mode.get()
    button_start.config(text="Mulai Pindah" if mode == "move" else "Mulai Salin")

def toggle_date_filter():
    state = "normal" if use_date_filter.get() else "disabled"
    entry_date_start.config(state=state)
    entry_date_end.config(state=state)

def copy_files():
    srcDir = entry_src.get()
    desDir = entry_dst.get()
    raw_text = text_strings.get("1.0", tk.END)
    reqStrings = [s.strip() for s in raw_text.strip().splitlines() if s.strip()]
    use_exact = var_exact.get()

    if not srcDir or not desDir:
        messagebox.showerror("Error", "Direktori asal dan tujuan harus diisi.")
        return

    if use_date_filter.get():
        try:
            start_date = datetime.strptime(entry_date_start.get(), "%Y-%m-%d").timestamp()
            end_date = datetime.strptime(entry_date_end.get(), "%Y-%m-%d").timestamp()
        except ValueError:
            messagebox.showerror("Error", "Format tanggal harus YYYY-MM-DD")
            return
    else:
        start_date = end_date = None

    file_list = []
    found_set = set()
    req_map = {req.lower(): req for req in reqStrings}  # mapping lowercase ke aslinya
    not_found = set(req_map.keys())

    for root_dir, _, files in os.walk(srcDir):
        for file in files:
            full_path = os.path.join(root_dir, file)
            file_lower = file.lower()

            if not reqStrings:
                match = True
            elif use_exact:
                match = any(file_lower == req.lower() for req in reqStrings)
            else:
                match = any(req.lower() in file_lower for req in reqStrings)

            if match:
                if use_date_filter.get():
                    created = os.path.getctime(full_path)
                    if not (start_date <= created <= end_date):
                        continue

                file_list.append(full_path)

                # Cek item yang ditemukan
                for req_lower in req_map:
                    if (file_lower == req_lower if use_exact else req_lower in file_lower):
                        found_set.add(req_lower)

    # Update not_found berdasarkan yang tidak ditemukan
    not_found -= found_set

    total = len(file_list)
    if total == 0:
        messagebox.showinfo("Info", "Tidak ada file yang cocok.")
        return

    os.makedirs(desDir, exist_ok=True)
    progress_bar["maximum"] = total
    progress_bar["value"] = 0
    copied_files = []

    start_time = time.time()

    for i, src_path in enumerate(file_list, start=1):
        try:
            filename = os.path.basename(src_path)
            dst_path = os.path.join(desDir, filename)
            if operation_mode.get() == "move":
                shutil.move(src_path, dst_path)
            else:
                shutil.copy(src_path, dst_path)
            copied_files.append(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memproses {filename}:\n{e}")
        progress_bar["value"] = i
        root.update_idletasks()

    end_time = time.time()
    elapsed = end_time - start_time

    messagebox.showinfo("Selesai", f"{len(copied_files)} file diproses:\n\n" + "\n".join(copied_files))

    if not_found:
        messagebox.showwarning("Nama Tidak Ditemukan", "Berikut nama yang tidak ditemukan:\n\n" +
                       "\n".join([req_map[n] for n in sorted(not_found)]))
                       
    progress_bar["value"] = 0
    label_duration.config(text=f"Selesai dalam {elapsed:.2f} detik")

# Setup window
root = tk.Tk()
root.title("File Finder")
def resource_path(rel_path):
    import sys
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return rel_path
# Logo
try:
    logo_img = PhotoImage(file=resource_path("logo.png"))
    root.iconphoto(True, logo_img)
    logo_label = tk.Label(root, image=logo_img)
    logo_label.grid(row=0, column=0, columnspan=3, pady=(10, 0))
except Exception as e:
    print(f"Gagal memuat logo: {e}")

# Form Direktori
tk.Label(root, text="Direktori Asal:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
entry_src = tk.Entry(root, width=50)
entry_src.grid(row=1, column=1, padx=5)
tk.Button(root, text="Browse", command=browse_src).grid(row=1, column=2, padx=5)

tk.Label(root, text="Direktori Tujuan:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
entry_dst = tk.Entry(root, width=50)
entry_dst.grid(row=2, column=1, padx=5)
tk.Button(root, text="Browse", command=browse_dst).grid(row=2, column=2, padx=5)

# Nama file
tk.Label(root, text="Nama File (pisahkan baris):").grid(row=3, column=0, sticky="ne", padx=5, pady=5)
text_strings = tk.Text(root, width=50, height=6)
text_strings.grid(row=3, column=1, columnspan=2, padx=5)

# Pencarian dan Mode
var_exact = tk.BooleanVar(value=False)
checkbox_exact = tk.Checkbutton(root, text="Tepat berisi (exact match)", variable=var_exact)
checkbox_exact.grid(row=4, column=1, sticky="w", padx=5, pady=(0, 0))

operation_mode = tk.StringVar(value="copy")
tk.Radiobutton(root, text="Salin", variable=operation_mode, value="copy", command=update_button_label).grid(row=5, column=1, sticky="w", padx=(5, 80))
tk.Radiobutton(root, text="Pindah", variable=operation_mode, value="move", command=update_button_label).grid(row=5, column=1, sticky="e", padx=(80, 5))

# Filter Tanggal
use_date_filter = tk.BooleanVar(value=False)
checkbox_date = tk.Checkbutton(root, text="Gunakan filter tanggal dibuat", variable=use_date_filter, command=toggle_date_filter)
checkbox_date.grid(row=6, column=1, sticky="w", padx=5)

tk.Label(root, text="Dari (YYYY-MM-DD):").grid(row=7, column=0, sticky="e", padx=5)
entry_date_start = tk.Entry(root, width=20, state="disabled")
entry_date_start.grid(row=7, column=1, sticky="w", padx=5)

tk.Label(root, text="Sampai (YYYY-MM-DD):").grid(row=8, column=0, sticky="e", padx=5)
entry_date_end = tk.Entry(root, width=20, state="disabled")
entry_date_end.grid(row=8, column=1, sticky="w", padx=5)

# Tombol & progress
button_start = tk.Button(root, text="Mulai Salin", command=start_copy, bg="lightgreen", width=20)
button_start.grid(row=9, column=1, pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=10, column=0, columnspan=3, pady=10)

label_duration = tk.Label(root, text="", fg="gray")
label_duration.grid(row=11, column=0, columnspan=3)

credit_label = tk.Label(root, text="Made with ❤️ Gilang Wahyu Prasetyo - BPS Tabalong", fg="gray")
credit_label.grid(row=12, column=0, columnspan=3, pady=(5, 10))

root.mainloop()
