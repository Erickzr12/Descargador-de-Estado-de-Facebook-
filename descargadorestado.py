import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import yt_dlp
import queue
import time

class DownloaderApp(tk.Tk):
    THEMES = {
        "Claro": {
            "bg": "#ffffff",
            "fg": "#000000",
            "btn_bg": "#e0e0e0",
            "btn_fg": "#000000",
            "entry_bg": "#ffffff",
            "entry_fg": "#000000"
        },
        "Oscuro": {
            "bg": "#2e2e2e",
            "fg": "#f0f0f0",
            "btn_bg": "#4d4d4d",
            "btn_fg": "#f0f0f0",
            "entry_bg": "#3a3a3a",
            "entry_fg": "#f0f0f0"
        },
        "Azul": {
            "bg": "#dbe9f4",
            "fg": "#0d1b2a",
            "btn_bg": "#457b9d",
            "btn_fg": "#ffffff",
            "entry_bg": "#f1faee",
            "entry_fg": "#0d1b2a"
        }
    }

    def __init__(self):
        super().__init__()
        self.title("FDownloader.Net Mini - Cola + Login + Pausa + Temas + Cookies")
        self.geometry("700x650")
        self.paused = False
        self.stop_event = threading.Event()

        self.create_widgets()
        self.apply_theme("Claro")

        self.download_queue = queue.Queue()
        self.is_downloading = False
        self.current_download_thread = None

    def create_widgets(self):
        # Tema selector
        theme_frame = tk.Frame(self)
        theme_frame.pack(padx=10, pady=5, anchor="e")
        tk.Label(theme_frame, text="Tema:").pack(side="left")
        self.theme_var = tk.StringVar(value="Claro")
        theme_menu = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=list(self.THEMES.keys()), state="readonly", width=10)
        theme_menu.pack(side="left")
        theme_menu.bind("<<ComboboxSelected>>", lambda e: self.apply_theme(self.theme_var.get()))

        # URL Input para cola
        tk.Label(self, text="Agregar URL a la cola:").pack(anchor="w", padx=10, pady=(10,0))
        url_frame = tk.Frame(self)
        url_frame.pack(fill="x", padx=10)
        self.url_entry = tk.Entry(url_frame, width=60)
        self.url_entry.pack(side="left", fill="x", expand=True)
        tk.Button(url_frame, text="Agregar", command=self.add_url_to_queue).pack(side="left", padx=5)

        # Lista de URLs en cola
        tk.Label(self, text="Cola de descargas:").pack(anchor="w", padx=10, pady=(10,0))
        self.queue_listbox = tk.Listbox(self, height=8)
        self.queue_listbox.pack(fill="both", padx=10)

        tk.Button(self, text="Eliminar URL seleccionada", command=self.remove_selected_url).pack(pady=(5,10))

        # Usuario y contraseña para login
        login_frame = tk.Frame(self)
        login_frame.pack(fill="x", padx=10)
        tk.Label(login_frame, text="Usuario (opcional):").grid(row=0, column=0, sticky="w")
        self.user_entry = tk.Entry(login_frame, width=30)
        self.user_entry.grid(row=0, column=1, padx=5, pady=2)
        tk.Label(login_frame, text="Contraseña (opcional):").grid(row=1, column=0, sticky="w")
        self.pass_entry = tk.Entry(login_frame, show="*", width=30)
        self.pass_entry.grid(row=1, column=1, padx=5, pady=2)

        # Selector de archivo de cookies
        cookies_frame = tk.Frame(self)
        cookies_frame.pack(fill="x", padx=10, pady=(10,0))
        tk.Label(cookies_frame, text="Archivo de cookies (opcional):").pack(side="left")
        self.cookies_path_var = tk.StringVar(value="")
        self.cookies_entry = tk.Entry(cookies_frame, textvariable=self.cookies_path_var)
        self.cookies_entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(cookies_frame, text="Examinar", command=self.browse_cookies_file).pack(side="left")

        # Botón para seleccionar carpeta destino
        dest_frame = tk.Frame(self)
        dest_frame.pack(fill="x", padx=10, pady=(10,0))
        tk.Label(dest_frame, text="Carpeta destino:").pack(side="left")
        self.dest_folder = tk.StringVar(value="Descargas")
        self.folder_entry = tk.Entry(dest_frame, textvariable=self.dest_folder)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(dest_frame, text="Examinar", command=self.browse_folder).pack(side="left")

        # Botón para cargar formatos de URL seleccionada en cola
        tk.Button(self, text="Cargar formatos de URL seleccionada", command=self.load_formats).pack(pady=(10,5))

        # Lista de formatos
        tk.Label(self, text="Formatos disponibles:").pack(anchor="w", padx=10)
        self.format_list = ttk.Combobox(self, state="readonly", width=90)
        self.format_list.pack(padx=10)

        # Botones para controlar descarga
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        self.download_btn = tk.Button(btn_frame, text="Descargar cola", state="disabled", command=self.start_queue_download)
        self.download_btn.pack(side="left", padx=5)
        self.pause_btn = tk.Button(btn_frame, text="Pausar", state="disabled", command=self.pause_download)
        self.pause_btn.pack(side="left", padx=5)
        self.resume_btn = tk.Button(btn_frame, text="Reanudar", state="disabled", command=self.resume_download)
        self.resume_btn.pack(side="left", padx=5)

        # Barra de progreso
        self.progress = ttk.Progressbar(self, length=600, mode="determinate")
        self.progress.pack(pady=10)

        # Estado (label)
        self.status_label = tk.Label(self, text="")
        self.status_label.pack()

    def apply_theme(self, theme_name):
        theme = self.THEMES.get(theme_name, self.THEMES["Claro"])
        bg = theme["bg"]
        fg = theme["fg"]
        btn_bg = theme["btn_bg"]
        btn_fg = theme["btn_fg"]
        entry_bg = theme["entry_bg"]
        entry_fg = theme["entry_fg"]

        self.configure(bg=bg)
        for widget in self.winfo_children():
            self.recursive_theme_apply(widget, bg, fg, btn_bg, btn_fg, entry_bg, entry_fg)

    def recursive_theme_apply(self, widget, bg, fg, btn_bg, btn_fg, entry_bg, entry_fg):
        try:
            cls = widget.winfo_class()
            if cls == 'TLabel' or cls == 'Label':
                widget.configure(background=bg, foreground=fg)
            elif cls == 'TButton' or cls == 'Button':
                widget.configure(background=btn_bg, foreground=btn_fg, activebackground=btn_fg, activeforeground=btn_bg)
            elif cls == 'TEntry' or cls == 'Entry':
                widget.configure(background=entry_bg, foreground=entry_fg, insertbackground=entry_fg)
            elif cls == 'TCombobox':
                widget.configure(background=entry_bg, foreground=entry_fg)
            elif cls == 'Listbox':
                widget.configure(background=entry_bg, foreground=entry_fg)
            elif cls == 'Frame':
                widget.configure(background=bg)
            for child in widget.winfo_children():
                self.recursive_theme_apply(child, bg, fg, btn_bg, btn_fg, entry_bg, entry_fg)
        except:
            pass

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.dest_folder.set(folder_selected)

    def browse_cookies_file(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de cookies",
            filetypes=[("Archivo cookies", "*.txt;*.cookie;*.cookies"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.cookies_path_var.set(file_path)

    def add_url_to_queue(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Por favor, introduce una URL válida")
            return
        self.queue_listbox.insert(tk.END, url)
        self.url_entry.delete(0, tk.END)
        self.download_btn.config(state="normal")

    def remove_selected_url(self):
        selected = self.queue_listbox.curselection()
        if not selected:
            messagebox.showinfo("Info", "Selecciona una URL para eliminar")
            return
        for index in reversed(selected):
            self.queue_listbox.delete(index)
        if self.queue_listbox.size() == 0:
            self.download_btn.config(state="disabled")

    def load_formats(self):
        selected = self.queue_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Selecciona una URL en la cola para cargar formatos")
            return
        url = self.queue_listbox.get(selected[0])
        ydl_opts = {}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get("formats", [])
                format_strings = []
                for f in formats:
                    # formato: format_id - ext - resolution - note
                    fs = f"{f.get('format_id')} - {f.get('ext')} - {f.get('resolution') or f.get('format_note') or ''}"
                    format_strings.append(fs)
                self.format_list['values'] = format_strings
                if format_strings:
                    self.format_list.current(0)
                self.status_label.config(text=f"Cargados {len(format_strings)} formatos")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar formatos: {e}")

    def validate_cookies(self):
        path = self.cookies_path_var.get()
        if not path:
            messagebox.showwarning("Cookies", "No has cargado archivo de cookies.")
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if "facebook.com" not in content and "instagram.com" not in content:
                    messagebox.showwarning("Cookies", "El archivo de cookies no contiene cookies de Facebook ni Instagram.")
                    return False
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo de cookies: {e}")
            return False
        return True

    def start_queue_download(self):
        if self.is_downloading:
            messagebox.showinfo("Descarga", "Ya se está descargando")
            return

        urls = [self.queue_listbox.get(i) for i in range(self.queue_listbox.size())]
        needs_cookies = any("facebook.com" in url or "instagram.com" in url for url in urls)
        if needs_cookies and not self.validate_cookies():
            return  # Cancela inicio si no hay cookies válidas

        self.paused = False
        self.stop_event.clear()
        self.is_downloading = True
        self.download_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.resume_btn.config(state="disabled")
        self.current_download_thread = threading.Thread(target=self.download_queue_worker)
        self.current_download_thread.start()

    def download_queue_worker(self):
        while self.queue_listbox.size() > 0:
            if self.stop_event.is_set():
                self.is_downloading = False
                self.update_ui_after_download()
                return

            if self.paused:
                time.sleep(0.5)
                continue

            url = self.queue_listbox.get(0)
            self.status_label.config(text=f"Descargando: {url}")

            ydl_opts = {
                "outtmpl": f"{self.dest_folder.get()}/%(title)s.%(ext)s",
                "progress_hooks": [self.progress_hook],
                "username": self.user_entry.get().strip() or None,
                "password": self.pass_entry.get().strip() or None,
            }
            cookies_path = self.cookies_path_var.get()
            if cookies_path:
                ydl_opts["cookiefile"] = cookies_path

            # Agregar formato si seleccionado
            selected_format = self.format_list.get()
            if selected_format:
                format_id = selected_format.split(" - ")[0]
                ydl_opts["format"] = format_id

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                messagebox.showerror("Error de descarga", f"Error descargando {url}:\n{e}")

            self.queue_listbox.delete(0)
            self.progress['value'] = 0

        self.is_downloading = False
        self.update_ui_after_download()
        self.status_label.config(text="Descargas finalizadas.")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            downloaded = d.get('downloaded_bytes', 0)
            percent = downloaded / total * 100
            self.progress['value'] = percent
        elif d['status'] == 'finished':
            self.progress['value'] = 100

    def update_ui_after_download(self):
        self.download_btn.config(state="normal" if self.queue_listbox.size() > 0 else "disabled")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")

    def pause_download(self):
        if self.is_downloading:
            self.paused = True
            self.pause_btn.config(state="disabled")
            self.resume_btn.config(state="normal")
            self.status_label.config(text="Descarga pausada.")

    def resume_download(self):
        if self.is_downloading and self.paused:
            self.paused = False
            self.pause_btn.config(state="normal")
            self.resume_btn.config(state="disabled")
            self.status_label.config(text="Descarga reanudada.")


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
