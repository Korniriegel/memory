import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import os
import random
import json
from PIL import Image
import sys
import os

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

assets_folder = os.path.join(base_path, "assets")
ui_assets_folder = os.path.join(base_path, "ui_assets")
highscore_file = os.path.join(base_path, "highscores.json")
icon_path = os.path.join(base_path, "memory.ico")

class MemoryGame(ctk.CTk):
    def __init__(self, rows=4, cols=4, tile_size=96):
        super().__init__()
        self.title("Memory")
        #Fenstergröße
        self.geometry("1280x720")
        self.resizable(True, True)

        #Spielparameter
        self.rows = rows
        self.cols = cols
        self.tile_size = tile_size

        #Spielvariablen
        self.moves = 0
        self.start_time = None
        self.timer_running = False
        self.revealed = []
        self.matched = []
        self.first = None
        self.deck = []
        self.buttons = []
        self.card_images = []

        # Highscores laden
        self.highscores = []
        if os.path.exists(highscore_file):
            with open(highscore_file, "r") as f:
                self.highscores = json.load(f)

        # Top-Frame für Start-Button/Labels
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(side="top", fill="x", padx=10, pady=10)
        ctk.CTkButton(top_frame, text="Spiel starten", command=self.reset).pack(side="left", pady=10)
        self.move_var = ctk.StringVar(value="Züge: 0")
        ctk.CTkLabel(top_frame, textvariable=self.move_var, font=("Segoe UI", 14)).pack(side="right", pady=5, padx=20)
        self.timer_var = ctk.StringVar(value="Zeit: 0.0s")
        ctk.CTkLabel(top_frame, textvariable=self.timer_var, font=("Segoe UI", 14)).pack(side="right", pady=5, padx=10)

        # Menü für Spielgröße
        menubar = tk.Menu(self)
        size_menu = tk.Menu(menubar, tearoff=0)
        for tiles in [4, 6, 8, 10, 12, 16, 18]:
            size_menu.add_command(label=f"{tiles} Kärtchen",
                                  command=lambda t=tiles: self.change_board_size(t))
        menubar.add_cascade(label="Spielgröße", menu=size_menu)
        def show_about():
            messagebox.showinfo("Über", "Memory-Spiel\n© 2025 Basti\nAlle Rechte vorbehalten\nE-Mail: korniriegel@gmail.com")
        menubar.add_command(label="Über", command=show_about)
        self.config(menu=menubar)

        # Spielfeld
        self.board = ctk.CTkFrame(self, fg_color="transparent")
        self.board.pack(expand=True)
        self.board.place(relx=0.5, rely=0.5, anchor="center")

        # Kartenrücken laden
        back_path = os.path.join(assets_folder, "back.png")
        if not os.path.exists(back_path):
            raise FileNotFoundError(f"Kartenrücken nicht gefunden: {back_path}")
        self.back_image = self.load_image(back_path, self.tile_size)

        # Kartenbilder laden
        self.load_card_images()

        # Buttons vorbereiten
        self._build_buttons()

    def load_image(self, path, size):
        pil_img = Image.open(path).convert("RGBA")
        pil_img = pil_img.resize((size, size))
        return ctk.CTkImage(light_image=pil_img, size=(size, size))

    def load_card_images(self):
        self.card_images = []
        for file in os.listdir(assets_folder):
            if file.lower().endswith(".jpg") and file != "back.jpg":
                path = os.path.join(assets_folder, file)
                self.card_images.append(self.load_image(path, self.tile_size))

    def change_board_size(self, total_tiles):
        cols = int(total_tiles ** 0.5)
        rows = total_tiles // cols
        if rows * cols < total_tiles:
            rows += 1
        self.rows, self.cols = rows, cols

        # Tile-Size basierend auf Fenstergröße
        max_width = 780
        max_height = 650
        tile_width = max_width // self.cols
        tile_height = max_height // self.rows
        self.tile_size = min(tile_width, tile_height)

        # Kartenrücken und Bilder skalieren
        self.back_image = self.load_image(os.path.join(assets_folder, "back.png"), self.tile_size)
        self.load_card_images()
        self._build_buttons()

    def _build_buttons(self):
        for widget in self.board.winfo_children():
            widget.destroy()

        self.buttons = []
        for r in range(self.rows):
            row_btns = []
            for c in range(self.cols):
                btn = ctk.CTkButton(
                    self.board,
                    image=self.back_image,
                    text="",
                    corner_radius=8,
                    fg_color="transparent",
                    width=self.tile_size,
                    height=self.tile_size,
                    command=lambda r=r, c=c: self.on_card_click(r, c)
                )
                btn.grid(row=r, column=c, padx=4, pady=4)
                btn.img_ref = self.back_image
                row_btns.append(btn)
            self.buttons.append(row_btns)

    def reset(self):
        pair_count = (self.rows * self.cols) // 2
        if pair_count > len(self.card_images):
            raise ValueError("Nicht genug Kartenbilder im Assets-Ordner!")
        deck = list(range(pair_count)) * 2
        random.shuffle(deck)
        self.deck = deck
        self.revealed = [[False]*self.cols for _ in range(self.rows)]
        self.matched = [[False]*self.cols for _ in range(self.rows)]
        self.first = None
        self.moves = 0
        self.move_var.set("Züge: 0")
        self.start_time = time.perf_counter()
        self.timer_running = True
        self._build_buttons()
        self._update_timer()

    def on_card_click(self, r, c):
        if self.revealed[r][c] or self.matched[r][c]:
            return
        self.revealed[r][c] = True
        self.buttons[r][c].configure(image=self.card_images[self.deck[self.index(r, c)]])
        if self.first is None:
            self.first = (r, c)
        else:
            r1, c1 = self.first
            if self.deck[self.index(r, c)] == self.deck[self.index(r1, c1)]:
                self.matched[r][c] = True
                self.matched[r1][c1] = True
            else:
                self.after(500, lambda: self.hide_cards((r1, c1), (r, c)))
            self.first = None

        self.moves += 1
        self.move_var.set(f"Züge: {self.moves}")

        if all(all(row) for row in self.matched):
            self.timer_running = False
            elapsed = time.perf_counter() - self.start_time
            self.show_win_window(elapsed)

    def hide_cards(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        self.revealed[r1][c1] = False
        self.revealed[r2][c2] = False
        self.buttons[r1][c1].configure(image=self.back_image)
        self.buttons[r2][c2].configure(image=self.back_image)

    def index(self, r, c):
        return r * self.cols + c

    def _update_timer(self):
        if self.timer_running:
            elapsed = time.perf_counter() - self.start_time
            self.timer_var.set(f"Zeit: {elapsed:.1f} s")
            self.after(100, self._update_timer)

    def show_win_window(self, elapsed):
        win = ctk.CTkToplevel(self)
        win.title("Super gemacht!")
        win.geometry("800x600")
        win.lift()
        win.focus_force()
        # Fenster in den Vordergrund holen
        win.lift()                 # hebt es vor andere Fenster
        win.attributes("-topmost", True)  # bleibt immer im Vordergrund
        win.focus_force()          # Tastaturfokus auf dieses Fenster

        ctk.CTkLabel(
            win,
            text=f"Alle Paare gefunden!\n{self.moves} Züge\nZeit: {elapsed:.1f} s",
            font=("Segoe UI", 14),
            justify="center"
        ).pack(pady=10)

        name_entry = ctk.CTkEntry(win, placeholder_text="Dein Name")
        name_entry.pack(pady=5)

        def save_score():
            name = name_entry.get() or "Unbekannt"
            self.highscores.append((name, elapsed, self.moves, self.rows, self.cols))
            self.highscores.sort(key=lambda x: (x[1], x[2]))
            # Highscore speichern
            with open(highscore_file, "w") as f:
                json.dump(self.highscores, f)
            win.destroy()
            self.show_highscores()

        ctk.CTkButton(win, text="Speichern", command=save_score).pack(pady=10)

        img_path = os.path.join(ui_assets_folder, "win.jpg")
        if os.path.exists(img_path):
            img = self.load_image(img_path, 400)
            ctk.CTkLabel(win, image=img, text="").pack(pady=5)

    def show_highscores(self):
        hs = ctk.CTkToplevel(self)
        hs.title("Highscores")
        hs.geometry("400x500")
        hs.lift()
        hs.focus_force()

        ctk.CTkLabel(hs, text="🏆 Highscores", font=("Segoe UI", 16)).pack(pady=10)
        for i, (name, elapsed, moves, rows, cols) in enumerate(self.highscores[:10], start=1):
            ctk.CTkLabel(
                hs,
                text=f"{i}. {name} – {elapsed:.1f}s – {moves} Züge – {rows}x{cols}",
                font=("Segoe UI", 12),
                anchor="w"
            ).pack(fill="x", padx=10, pady=2)

if __name__ == "__main__":
    app = MemoryGame(rows=4, cols=4, tile_size=96)
    app.mainloop()
