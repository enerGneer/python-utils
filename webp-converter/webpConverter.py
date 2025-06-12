import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, messagebox
from PIL import Image
import sys

if sys.platform == "darwin":
    os.system("open -g -a Terminal") 

def convert_to_webp(target_path):
    if not target_path:
        return
    
    target_path = target_path.strip("{}") 
    converted_count = 0

    if os.path.isdir(target_path):  # folder
        for filename in os.listdir(target_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):  # JPG, PNG 필터링
                img_path = os.path.join(target_path, filename)
                webp_filename = os.path.splitext(filename)[0] + ".webp"
                webp_path = os.path.join(target_path, webp_filename)

                try:
                    with Image.open(img_path) as img:
                        img.save(webp_path, "WEBP", quality=80)
                        converted_count += 1
                except Exception as e:
                    messagebox.showwarning("エラー", f"❌ {filename} の変換に失敗しました: {str(e)}")
    
    elif os.path.isfile(target_path) and target_path.lower().endswith(('.jpg', '.jpeg', '.png')):  # 파일일 경우
        folder_path = os.path.dirname(target_path)  
        filename = os.path.basename(target_path) 

        webp_filename = os.path.splitext(filename)[0] + ".webp"
        webp_path = os.path.join(folder_path, webp_filename)

        try:
            with Image.open(target_path) as img:
                img.save(webp_path, "WEBP", quality=80)
                converted_count += 1
        except Exception as e:
            messagebox.showwarning("エラー", f"❌ {filename} の変換に失敗しました: {str(e)}")

    # error
    if converted_count == 0:
        messagebox.showinfo("お知らせ", "📢 変換できる画像がありません。(JPG/PNGファイルが見つかりません)")
    else:
        messagebox.showinfo("完了", f"🎉 {converted_count} 枚の画像がWEBPに変換されました！")

def on_drop(event):
    """DnD event handler"""
    dropped_data = event.data.strip("{}") 

    paths = dropped_data.split()
    for path in paths:
        convert_to_webp(path)

def select_folder():
    """Select folder"""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        convert_to_webp(folder_selected)

# GUI
root = TkinterDnD.Tk()
root.title("WebP変換ツール")

# Window
win_width = 600
win_height = 400

# Position
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
pos_x = (screen_width // 2) - (win_width // 2)
pos_y = (screen_height // 2) - (win_height // 2)

root.geometry(f"{win_width}x{win_height}+{pos_x}+{pos_y}")

label = tk.Label(root, text="📂 ここにフォルダまたは画像をドラッグ＆ドロップ", bg="#f0f0f0", fg="black", font=("Arial", 12))
label.pack(expand=True, fill="both", padx=20, pady=50)

label.drop_target_register(DND_FILES)
label.dnd_bind("<<Drop>>", on_drop)

root.update_idletasks()
root.mainloop()
