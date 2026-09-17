# -*- coding: utf-8 -*-
"""
picpress - Photo Compressor
Fast, modern batch image compression. Dark UI. Drag & Drop.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import shutil
import io
import base64
from pathlib import Path
from PIL import Image, ImageTk

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    TkinterDnD = None
    DND_FILES = None

# ── Palette ──────────────────────────────────────────────────────────────────
BG         = "#191919"
SURFACE    = "#202020"
RAISED     = "#2A2A2A"
BORDER     = "#333333"
TEXT       = "#FFFFFF"
TEXT2      = "#A0A0A0"
ACCENT     = "#2783DE"
ACCENT_HOV = "#1a6ab8"
GREEN      = "#46A171"
RED        = "#E56458"
ORANGE     = "#D5803B"

if sys.platform == "win32":
    FF = "Segoe UI"
elif sys.platform == "darwin":
    FF = "Helvetica Neue"
else:
    FF = "DejaVu Sans"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

# ── Embedded bolt icon (32x32 PNG, base64) ─────────────────────────────────────
_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADT0lEQVR4nL2XS4gcVRSGv3NvVVf3"
    "9GN6ZtJBRuNCRAZBEzCKIkhkEpr4wIUiMviAhAk+NlkEdSEEiS6yM64N4iarLFy4UMGVgiLixscE"
    "MUQdH8wYZ6a7uquru+re66JcuFCmqmaSsyxunfNx7v+fOiXz8/OOXQgRcCUyqd0qnphy7+4YQASMgRvb"
    "9voDKIEoFhb2pXTvHhGOBFUw484AVAbw8jMhkRXSVJCiOcoW1wq2BkL3npijR0Z8vVKhFrjCQiwN"
    "4ADt4I2XevT7itU1j4rvsNcDwNOw0VcsdSPuOJTwzSWfcCR4uniuwgAiMEnhhrbh1eU+zsKVVc04"
    "EaSoAMoAaAW9UHHyqZCbbjNIBD/84mOhsAALAyiBwUg4cOuEE08PMRGQwqWfPHyvuAALA4iCJIHT"
    "y32CGYdYSELh5z88fO8aj2KtYLMvPHxfTPdoTLolqADWrirWNhQVr7gDcgMIkFqoB47TL/RBZzYk"
    "gCu/evQihS7hgNwASkM4VDz/2JCF/QlmE8Q6TAIrl32SVNAqc0hRJ3h5DhkDjZrlwy+rfPJEgAZ6"
    "Q2HxrjFaHBObWdMYcAi+zn8XuQAg08CPv3s4lw2i9U3FqaUBX3xbYW/TMlO3pBYCH/7s59e2FFlI"
    "RDIrJil0WpbP3lsHD8wYjIN623H27RZvXWzQrDtsji907g5AZjNR0Bsqjj8ypLXPwgBoAHPw/oUa"
    "5y42aEzlKw4lJqGx0Kxalh6KIIVJLNCAzz8KWD4zS7VazIuFALSCMBIeODDm9v0JaShU2o7L33k8"
    "+9osojN9FBlIxTogYI3w3KMRzgMVODbWFEun5rg6UFSD/K0vDKAERjEs3Jxw+P4YJmBT4dgrs3y/"
    "6tOacpgSi2l+AAXDWPHk4Yhgr0MUnHy9zcdfVZmbtqTXeitODOxpWh7vjpAqnD3X5PwHdTqzliQt"
    "VzwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACj/7gBJRU5ErkJggg=="
)

_ICON_REF = None  # keep reference to prevent GC


def _resource_path(filename):
    """Return correct path for resources whether running from source or PyInstaller EXE."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).parent / filename


def _apply_icon_now(root):
    """Actually apply the icon — called directly OR via after() delay for EXE."""
    global _ICON_REF
    applied = False

    # Method 1: iconbitmap with .ico (best for Windows taskbar + title bar)
    try:
        ico = _resource_path("icon.ico")
        if ico.exists():
            root.wm_iconbitmap(str(ico))
            applied = True
    except Exception:
        pass

    # Method 2: iconphoto with embedded PNG (fallback / complement)
    if not applied:
        try:
            data = base64.b64decode(_ICON_B64)
            pil_img = Image.open(io.BytesIO(data))
            _ICON_REF = ImageTk.PhotoImage(pil_img)
            root.iconphoto(True, _ICON_REF)
        except Exception:
            pass


def _set_app_icon(root):
    """Set the window + taskbar icon. Works with TkinterDnD on Windows."""
    # On Windows, tell the taskbar this is a distinct app (not just python.exe)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                u"picpress.PhotoCompressor.1")
        except Exception:
            pass

    # Apply immediately (works for run.bat / source mode)
    _apply_icon_now(root)

    # Also apply after a short delay: TkinterDnD.Tk() can reset the window
    # handle during init, wiping the icon — the delay re-applies it safely.
    root.after(150, lambda: _apply_icon_now(root))
    root.after(500, lambda: _apply_icon_now(root))  # extra safety for EXE


# ── Utilities ─────────────────────────────────────────────────────────────────
def human_size(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "{:.1f} {}".format(n, u)
        n /= 1024
    return "{:.1f} TB".format(n)


def parse_dnd(raw):
    paths = []
    raw = raw.strip()
    i = 0
    while i < len(raw):
        if raw[i] == "{":
            end = raw.index("}", i)
            paths.append(raw[i + 1:end])
            i = end + 2
        else:
            end = raw.find(" ", i)
            if end == -1:
                paths.append(raw[i:])
                break
            paths.append(raw[i:end])
            i = end + 1
    return [p for p in paths if Path(p).suffix.lower() in IMG_EXTS]


# ── Compression engine ────────────────────────────────────────────────────────
def compress_image(src, dst, method, quality):
    img = Image.open(src)
    orig_size = os.path.getsize(src)
    exif = img.info.get("exif", b"")
    has_alpha = img.mode in ("RGBA", "LA", "PA")
    ex = {"exif": exif} if exif else {}

    def to_rgb(im):
        return im.convert("RGB") if im.mode != "RGB" else im

    def to_rgba(im):
        return im.convert("RGBA") if im.mode != "RGBA" else im

    if method == "webp":
        out = to_rgba(img) if has_alpha else to_rgb(img)
        out.save(dst, "WEBP", method=6, quality=quality, lossless=False, **ex)
        return orig_size, os.path.getsize(dst), "WebP"

    if method == "png_lossless":
        img.save(dst, "PNG", optimize=True, compress_level=9)
        return orig_size, os.path.getsize(dst), "PNG lossless"

    if method == "jpeg":
        to_rgb(img).save(dst, "JPEG", quality=quality,
                         optimize=True, progressive=True,
                         subsampling=0, **ex)
        return orig_size, os.path.getsize(dst), "JPEG optimized"

    # Smart
    candidates = []
    b1 = io.BytesIO()
    (to_rgba(img) if has_alpha else to_rgb(img)).save(
        b1, "WEBP", method=6, quality=quality, lossless=False, **ex)
    candidates.append((b1.tell(), "WebP (smart)", b1, ".webp"))

    b2 = io.BytesIO()
    img.save(b2, "PNG", optimize=True, compress_level=9)
    candidates.append((b2.tell(), "PNG lossless (smart)", b2, ".png"))

    if not has_alpha:
        b3 = io.BytesIO()
        to_rgb(img).save(b3, "JPEG", quality=quality,
                         optimize=True, progressive=True,
                         subsampling=0, **ex)
        candidates.append((b3.tell(), "JPEG (smart)", b3, ".jpg"))

    candidates.sort(key=lambda x: x[0])
    best_sz, best_lbl, best_buf, best_ext = candidates[0]

    if best_sz < orig_size:
        final = Path(dst).with_suffix(best_ext)
        best_buf.seek(0)
        final.write_bytes(best_buf.read())
        return orig_size, best_sz, best_lbl

    shutil.copy2(src, dst)
    return orig_size, orig_size, "{} (already optimal)".format(img.format or "orig")


# ── Canvas helpers ────────────────────────────────────────────────────────────
def draw_dashed_rect(canvas, x1, y1, x2, y2, r=12, color="#555", dash=(8, 5)):
    kw = dict(style="arc", outline=color, dash=dash)
    canvas.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90,  **kw)
    canvas.create_arc(x2-2*r,  y1,      x2,     y1+2*r, start=0,   extent=90,  **kw)
    canvas.create_arc(x1,      y2-2*r,  x1+2*r, y2,     start=180, extent=90,  **kw)
    canvas.create_arc(x2-2*r,  y2-2*r,  x2,     y2,     start=270, extent=90,  **kw)
    lk = dict(fill=color, dash=dash)
    canvas.create_line(x1+r, y1,   x2-r, y1,   **lk)
    canvas.create_line(x2,   y1+r, x2,   y2-r, **lk)
    canvas.create_line(x1+r, y2,   x2-r, y2,   **lk)
    canvas.create_line(x1,   y1+r, x1,   y2-r, **lk)


# ── Drop zone ─────────────────────────────────────────────────────────────────
class DropZone(tk.Canvas):
    def __init__(self, parent, on_files, **kw):
        super().__init__(parent, bg=RAISED, highlightthickness=0, **kw)
        self.on_files = on_files
        self._hover = False
        self._active = False
        self.bind("<Configure>", lambda _: self._draw())
        self.bind("<Button-1>",  self._browse)
        self.bind("<Enter>",     lambda _: self._set_hover(True))
        self.bind("<Leave>",     lambda _: self._set_hover(False))
        if DND_AVAILABLE:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<DragEnter>>", self._dnd_enter)
            self.dnd_bind("<<DragLeave>>", self._dnd_leave)
            self.dnd_bind("<<Drop>>",      self._dnd_drop)

    def _set_hover(self, v):
        self._hover = v
        self._draw()

    def _dnd_enter(self, event):
        self._active = True
        self._draw()
        return event.action

    def _dnd_leave(self, _):
        self._active = False
        self._draw()

    def _dnd_drop(self, event):
        self._active = False
        self._draw()
        paths = parse_dnd(event.data)
        if paths:
            self.on_files(paths)

    def _draw(self):
        self.after_idle(self.__draw)

    def __draw(self):
        self.delete("all")
        w = self.winfo_width()  or 600
        h = self.winfo_height() or 150
        hi = self._hover or self._active
        self.configure(bg="#1a2a3a" if self._active else RAISED)
        draw_dashed_rect(self, 10, 10, w-10, h-10,
                         color=ACCENT if hi else BORDER)
        cx, cy = w // 2, h // 2
        self.create_text(cx, cy-28, text="\U0001f4c1",
                         font=(FF, 26), fill=ACCENT if hi else TEXT2)
        if DND_AVAILABLE:
            line1 = "Drop images here  \u00b7  or click to browse"
        else:
            line1 = "Click to browse images"
        self.create_text(cx, cy+9,  text=line1,
                         font=(FF, 12), fill=TEXT if hi else TEXT2)
        self.create_text(cx, cy+29,
                         text="JPEG  \u00b7  PNG  \u00b7  WebP  \u00b7  BMP  \u00b7  TIFF",
                         font=(FF, 9), fill=BORDER)
        if not DND_AVAILABLE:
            self.create_text(cx, h-14,
                             text="pip install tkinterdnd2  for drag & drop",
                             font=(FF, 8), fill=ORANGE)

    def _browse(self, _=None):
        files = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif"),
                ("All files", "*.*"),
            ])
        if files:
            self.on_files(list(files))


# ── File row ──────────────────────────────────────────────────────────────────
class FileRow(tk.Frame):
    def __init__(self, parent, path, remove_cb, **kw):
        super().__init__(parent, bg=RAISED, **kw)
        self.path = path
        self._status = tk.StringVar(value="Pending")
        self._detail = tk.StringVar(value="")
        name = Path(path).name
        if len(name) > 44:
            name = name[:41] + "\u2026"
        tk.Label(self, text="\U0001f5bc", bg=RAISED, fg=TEXT2,
                 font=(FF, 13)).pack(side="left", padx=(10, 6), pady=8)
        col = tk.Frame(self, bg=RAISED)
        col.pack(side="left", fill="x", expand=True)
        tk.Label(col, text=name, bg=RAISED, fg=TEXT,
                 font=(FF, 11), anchor="w").pack(fill="x")
        tk.Label(col, textvariable=self._detail, bg=RAISED, fg=TEXT2,
                 font=(FF, 9), anchor="w").pack(fill="x")
        self._slbl = tk.Label(self, textvariable=self._status, bg=RAISED,
                              fg=TEXT2, font=(FF, 10), width=20, anchor="e")
        self._slbl.pack(side="right", padx=(4, 10))
        tk.Button(self, text="\u2715", bg=RAISED, fg=TEXT2,
                  relief="flat", bd=0, font=(FF, 9), cursor="hand2",
                  activebackground=RAISED, activeforeground=RED,
                  command=lambda: remove_cb(path)).pack(side="right", padx=2)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")

    def set_running(self):
        self._status.set("Compressing\u2026")
        self._slbl.config(fg=ACCENT)

    def set_done(self, orig, comp, fmt):
        pct = (orig - comp) / orig * 100 if orig else 0
        self._status.set("\u2212{:.1f}%  \u2713".format(pct))
        self._slbl.config(fg=GREEN)
        self._detail.set("{}  \u2192  {}   \u00b7   {}".format(
            human_size(orig), human_size(comp), fmt))

    def set_error(self, msg):
        self._status.set("Error")
        self._slbl.config(fg=RED)
        self._detail.set(str(msg)[:80])


# ── Progress bar ──────────────────────────────────────────────────────────────
class PBar(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=RAISED, height=5,
                         highlightthickness=0, bd=0, **kw)
        self._pct = 0.0
        self.bind("<Configure>", lambda _: self._draw())

    def set(self, pct):
        self._pct = max(0.0, min(1.0, pct))
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()  or 1
        h = self.winfo_height() or 5
        self.create_rectangle(0, 0, w, h, fill=RAISED, outline="")
        if self._pct > 0:
            self.create_rectangle(0, 0, int(w * self._pct), h,
                                  fill=ACCENT, outline="")


# ── App ───────────────────────────────────────────────────────────────────────
_AppBase = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class PicPress(_AppBase):
    def __init__(self):
        super().__init__()
        self.title("picpress")
        self.geometry("880x700")
        self.minsize(700, 520)
        self.configure(bg=BG)
        _set_app_icon(self)
        self._files = []
        self._rows = {}
        self._running = False
        self._out_dir = None
        self._build()
        self._apply_style()

    def _apply_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("P.Horizontal.TScale",
                    background=BG, troughcolor=RAISED,
                    sliderlength=16, sliderrelief="flat", borderwidth=0)
        s.configure("P.Vertical.TScrollbar",
                    background=RAISED, troughcolor=SURFACE,
                    arrowcolor=TEXT2, borderwidth=0, relief="flat")
        s.map("P.Vertical.TScrollbar", background=[("active", BORDER)])

    def _build(self):
        hdr = tk.Frame(self, bg=SURFACE)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=BORDER, height=1).pack(fill="x", side="bottom")
        hf = tk.Frame(hdr, bg=SURFACE)
        hf.pack(fill="x", padx=24, pady=14)
        tk.Label(hf, text="\u26a1  picpress",
                 bg=SURFACE, fg=TEXT,
                 font=(FF, 19, "bold")).pack(side="left")
        tk.Label(hf, text="Maximum compression  \u00b7  minimum quality loss",
                 bg=SURFACE, fg=TEXT2,
                 font=(FF, 11)).pack(side="left", padx=14)
        dnd_text  = "\u2713 Drag & Drop ready" if DND_AVAILABLE \
                    else "\u26a0 Install tkinterdnd2 for drag & drop"
        dnd_color = GREEN if DND_AVAILABLE else ORANGE
        tk.Label(hf, text=dnd_text, bg=SURFACE, fg=dnd_color,
                 font=(FF, 9)).pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        self._dz = DropZone(left, on_files=self._add_files, height=150)
        self._dz.pack(fill="x")

        lhdr = tk.Frame(left, bg=BG)
        lhdr.pack(fill="x", pady=(14, 6))
        self._list_lbl = tk.Label(lhdr, text="Queue  (0 files)",
                                  bg=BG, fg=TEXT, font=(FF, 12, "bold"))
        self._list_lbl.pack(side="left")
        tk.Button(lhdr, text="Clear all", bg=RAISED, fg=TEXT2,
                  relief="flat", bd=0, padx=10, font=(FF, 10),
                  cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT,
                  command=self._clear_all).pack(side="right")

        lf = tk.Frame(left, bg=RAISED)
        lf.pack(fill="both", expand=True)
        self._sc = tk.Canvas(lf, bg=RAISED, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(lf, orient="vertical",
                           command=self._sc.yview,
                           style="P.Vertical.TScrollbar")
        self._sc.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._sc.pack(side="left", fill="both", expand=True)
        self._inner = tk.Frame(self._sc, bg=RAISED)
        self._win = self._sc.create_window((0, 0), window=self._inner,
                                           anchor="nw")
        self._inner.bind(
            "<Configure>",
            lambda _: self._sc.configure(
                scrollregion=self._sc.bbox("all")))
        self._sc.bind(
            "<Configure>",
            lambda e: self._sc.itemconfig(self._win, width=e.width))
        self.bind_all(
            "<MouseWheel>",
            lambda e: self._sc.yview_scroll(
                int(-1 * (e.delta / 120)), "units"))

        tk.Frame(body, bg=BORDER, width=1).pack(
            side="left", fill="y", padx=16)

        right = tk.Frame(body, bg=BG, width=228)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        def sec(label):
            tk.Label(right, text=label, bg=BG, fg=TEXT2,
                     font=(FF, 8, "bold")).pack(anchor="w", pady=(18, 4))
            tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=(0, 8))

        sec("COMPRESSION METHOD")
        self._method = tk.StringVar(value="smart")
        for lbl, val in [
            ("\u2728  Smart  (auto best format)",        "smart"),
            ("\U0001f310  WebP  \u2013 saves as .webp",  "webp"),
            ("\U0001f535  JPEG  \u2013 saves as .jpg",   "jpeg"),
            ("\U0001f7e2  PNG   \u2013 lossless .png",   "png_lossless"),
        ]:
            tk.Radiobutton(right, text=lbl,
                           variable=self._method, value=val,
                           bg=BG, fg=TEXT, selectcolor=RAISED,
                           activebackground=BG, activeforeground=TEXT,
                           font=(FF, 10), relief="flat", bd=0,
                           pady=3).pack(anchor="w")

        self._hint_lbl = tk.Label(right, text="",
                                  bg=BG, fg=ORANGE, font=(FF, 8),
                                  wraplength=200, justify="left")
        self._hint_lbl.pack(anchor="w", pady=(4, 0))
        self._method.trace_add("write", self._update_hint)
        self._update_hint()

        sec("QUALITY   (JPEG / WebP)")
        self._quality = tk.IntVar(value=85)
        qrow = tk.Frame(right, bg=BG)
        qrow.pack(fill="x")
        self._qlbl = tk.Label(qrow, text="85", bg=BG, fg=ACCENT,
                              font=(FF, 13, "bold"), width=4)
        self._qlbl.pack(side="right")
        ttk.Scale(qrow, from_=60, to=99,
                  variable=self._quality, orient="horizontal",
                  style="P.Horizontal.TScale",
                  command=lambda v:
                      self._qlbl.config(
                          text=str(int(float(v)))
                      )).pack(fill="x", expand=True)
        tk.Label(right, text="Higher = better quality, larger file",
                 bg=BG, fg=TEXT2, font=(FF, 8)).pack(anchor="w", pady=(2, 0))

        sec("OUTPUT FOLDER")
        self._out_var = tk.StringVar(value="Same folder as source")
        orow = tk.Frame(right, bg=BG)
        orow.pack(fill="x")
        tk.Label(orow, textvariable=self._out_var,
                 bg=RAISED, fg=TEXT2, font=(FF, 9),
                 wraplength=150, justify="left",
                 padx=6, pady=4).pack(side="left", fill="x", expand=True)
        tk.Button(orow, text="\u2026", bg=RAISED, fg=TEXT,
                  relief="flat", bd=0, padx=8, cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT,
                  command=self._pick_out).pack(side="right")

        sec("FILENAME SUFFIX")
        self._suffix = tk.StringVar(value="")
        tk.Entry(right, textvariable=self._suffix,
                 bg=RAISED, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=(FF, 10), bd=4).pack(fill="x")
        tk.Label(right,
                 text="Leave blank to keep the original filename.",
                 bg=BG, fg=TEXT2, font=(FF, 8),
                 wraplength=200, justify="left").pack(anchor="w", pady=(2, 0))
        tk.Label(right,
                 text="Auto-adds _compressed only to prevent overwrite.",
                 bg=BG, fg=TEXT2, font=(FF, 8),
                 wraplength=200, justify="left").pack(anchor="w")

        bar = tk.Frame(self, bg=SURFACE)
        bar.pack(fill="x")
        tk.Frame(bar, bg=BORDER, height=1).pack(fill="x", side="top")
        self._pbar = PBar(bar)
        self._pbar.pack(fill="x")
        brow = tk.Frame(bar, bg=SURFACE)
        brow.pack(fill="x", padx=20, pady=12)
        self._msg = tk.Label(brow, text="Add images to get started.",
                             bg=SURFACE, fg=TEXT2, font=(FF, 10))
        self._msg.pack(side="left")
        self._go_btn = tk.Button(
            brow, text="  Compress All  ",
            bg=ACCENT, fg="white",
            activebackground=ACCENT_HOV, activeforeground="white",
            relief="flat", bd=0, padx=18, pady=9,
            font=(FF, 11, "bold"), cursor="hand2",
            command=self._start)
        self._go_btn.pack(side="right")
        tk.Button(brow, text="Add Images",
                  bg=RAISED, fg=TEXT,
                  activebackground=BORDER, activeforeground=TEXT,
                  relief="flat", bd=0, padx=12, pady=9,
                  font=(FF, 10), cursor="hand2",
                  command=lambda: self._dz._browse()
                  ).pack(side="right", padx=(0, 10))

    def _update_hint(self, *_):
        hints = {
            "smart":        "Tries WebP, PNG, JPEG. Picks the smallest.",
            "webp":         "Output saved as .webp",
            "jpeg":         "Output saved as .jpg",
            "png_lossless": "Output saved as .png",
        }
        self._hint_lbl.config(text=hints.get(self._method.get(), ""))

    def _add_files(self, paths):
        for p in paths:
            if p not in self._files:
                self._files.append(p)
                row = FileRow(self._inner, p, remove_cb=self._remove_file)
                row.pack(fill="x")
                self._rows[p] = row
        self._update_label()

    def _remove_file(self, path):
        if self._running:
            return
        self._files = [f for f in self._files if f != path]
        if path in self._rows:
            self._rows.pop(path).destroy()
        self._update_label()

    def _clear_all(self):
        if self._running:
            return
        for w in self._inner.winfo_children():
            w.destroy()
        self._files.clear()
        self._rows.clear()
        self._update_label()
        self._msg.config(text="Add images to get started.", fg=TEXT2)
        self._pbar.set(0)

    def _update_label(self):
        n = len(self._files)
        s = "s" if n != 1 else ""
        self._list_lbl.config(text="Queue  ({} file{})".format(n, s))

    def _pick_out(self):
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            self._out_dir = d
            short = d if len(d) < 28 else "\u2026" + d[-26:]
            self._out_var.set(short)

    def _start(self):
        if self._running:
            return
        if not self._files:
            messagebox.showinfo("picpress", "Add images first.")
            return
        self._running = True
        self._go_btn.config(state="disabled", text="  Working\u2026  ")
        self._pbar.set(0)
        threading.Thread(target=self._run_all, daemon=True).start()

    def _run_all(self):
        method  = self._method.get()
        quality = self._quality.get()
        suffix  = self._suffix.get()
        total   = len(self._files)
        done = orig_total = saved_total = 0
        EXT = {
            "webp":         ".webp",
            "jpeg":         ".jpg",
            "png_lossless": ".png",
            "smart":        None,
        }
        for i, src in enumerate(self._files, 1):
            row = self._rows[src]
            self.after(0, row.set_running)
            self.after(0, self._msg.config,
                       {"text": "Compressing {} / {}\u2026".format(i, total),
                        "fg":   ACCENT})
            try:
                p       = Path(src)
                out_d   = Path(self._out_dir) if self._out_dir else p.parent
                stem    = p.stem + suffix
                out_ext = EXT[method] if EXT[method] else p.suffix
                dst     = out_d / (stem + out_ext)
                if dst.resolve() == p.resolve():
                    dst = out_d / (p.stem + "_compressed" + out_ext)
                orig, comp, fmt = compress_image(
                    src, str(dst), method, quality)
                orig_total  += orig
                saved_total += max(0, orig - comp)
                self.after(0, row.set_done, orig, comp, fmt)
            except Exception as ex:
                self.after(0, row.set_error, ex)
            done += 1
            self.after(0, self._pbar.set, done / total)

        pct = saved_total / orig_total * 100 if orig_total else 0
        s   = "s" if total != 1 else ""
        msg = "\u2713  Done \u2014 saved {} ({:.1f}%) across {} file{}.".format(
            human_size(saved_total), pct, total, s)
        self.after(0, self._msg.config, {"text": msg, "fg": GREEN})
        self.after(0, self._go_btn.config,
                   {"state": "normal", "text": "  Compress All  "})
        self._running = False


if __name__ == "__main__":
    PicPress().mainloop()
