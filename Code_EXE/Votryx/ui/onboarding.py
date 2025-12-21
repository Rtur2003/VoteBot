"""Onboarding views for VOTRYX."""

import tkinter as tk
from tkinter import ttk

from ui.strings import STRINGS


class _BaseOnboardingView(tk.Frame):
    def __init__(
        self,
        app,
        parent,
        title,
        subtitle,
        bullets,
        cta_text,
        cta_command,
        hero_image=None,
    ):
        super().__init__(parent, bg=app.colors["bg"])
        self.app = app
        self.colors = app.colors
        self._bg_job = None
        self._reveal_job = None
        self._reveal_index = 0
        self._bullet_labels = []
        self._wrap_labels = []
        self._hero_image = hero_image
        self._hero_width = None
        if hero_image is not None:
            try:
                self._hero_width = int(hero_image.width())
            except Exception:
                self._hero_width = None

        self._canvas = tk.Canvas(
            self,
            bg=self.colors["bg"],
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self._canvas.pack(fill="both", expand=True)

        self._content = tk.Frame(self._canvas, bg=self.colors["bg"])
        self._content_id = self._canvas.create_window((0, 0), window=self._content, anchor="center")

        self._build_content(title, subtitle, bullets, cta_text, cta_command, hero_image)
        self._canvas.bind("<Configure>", self._on_resize)

    def _build_content(self, title, subtitle, bullets, cta_text, cta_command, hero_image):
        if hero_image is not None:
            self._content.columnconfigure(0, weight=1)
            self._content.columnconfigure(1, weight=0)
            self._content.rowconfigure(0, weight=1)
            body = tk.Frame(self._content, bg=self.colors["bg"])
            body.grid(row=0, column=0, sticky="nsew")
            body.columnconfigure(0, weight=1)

            hero_frame = tk.Frame(
                self._content,
                bg=self.colors["panel"],
                highlightthickness=1,
                highlightbackground=self.colors["border"],
            )
            hero_frame.grid(row=0, column=1, sticky="ne", padx=(24, 0))
            hero_label = tk.Label(hero_frame, image=hero_image, bg=self.colors["panel"], bd=0)
            hero_label.pack(padx=16, pady=16)
            self._hero_label = hero_label
        else:
            self._content.columnconfigure(0, weight=1)
            body = self._content
            body.columnconfigure(0, weight=1)

        title_label = tk.Label(
            body,
            text=title,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Bahnschrift", 28, "bold"),
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = tk.Label(
            body,
            text=subtitle,
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Bahnschrift", 12),
            wraplength=720,
            justify="left",
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(4, 16))
        self._wrap_labels.append(subtitle_label)

        bullets_frame = tk.Frame(body, bg=self.colors["bg"])
        bullets_frame.grid(row=2, column=0, sticky="w")
        for idx, line in enumerate(bullets):
            label = tk.Label(
                bullets_frame,
                text=f"- {line}",
                bg=self.colors["bg"],
                fg=self.colors["text"],
                font=("Bahnschrift", 11),
                anchor="w",
                justify="left",
                wraplength=720,
            )
            label.grid(row=idx, column=0, sticky="w", pady=(0, 6))
            label.grid_remove()
            self._bullet_labels.append(label)
            self._wrap_labels.append(label)

        cta = ttk.Button(
            body,
            text=cta_text,
            command=cta_command,
            style="Accent.TButton",
        )
        cta.grid(row=3, column=0, sticky="w", pady=(18, 0), ipadx=12, ipady=4)

    def _on_resize(self, event):
        width = max(1, event.width)
        height = max(1, event.height)
        if self._bg_job is not None:
            try:
                self.after_cancel(self._bg_job)
            except Exception:
                pass
        self._bg_job = self.after(80, lambda: self._draw_background(width, height))

    def _draw_background(self, width, height):
        self._bg_job = None
        self._canvas.delete("bg")
        steps = 28
        top = self.colors["bg"]
        bottom = self.colors["panel"]
        for step in range(steps):
            t = step / max(1, steps - 1)
            color = _blend_hex(top, bottom, t)
            y0 = int(height * (step / steps))
            y1 = int(height * ((step + 1) / steps))
            self._canvas.create_rectangle(0, y0, width, y1, fill=color, outline="", tags="bg")

        self._canvas.create_oval(
            int(width * 0.68),
            int(height * 0.1),
            int(width * 0.94),
            int(height * 0.36),
            outline=self.colors["accent2"],
            width=2,
            tags="bg",
        )
        self._canvas.create_oval(
            int(width * 0.08),
            int(height * 0.62),
            int(width * 0.32),
            int(height * 0.86),
            outline=self.colors["accent"],
            width=2,
            tags="bg",
        )

        max_width = 1080 if self._hero_image else 980
        min_width = 720 if self._hero_image else 600
        content_width = min(max_width, max(min_width, width - 160))
        self._canvas.coords(self._content_id, width // 2, height // 2)
        self._canvas.itemconfigure(self._content_id, width=content_width)
        if self._hero_image:
            hero_width = self._hero_width or int(content_width * 0.35)
            text_width = max(320, content_width - hero_width - 80)
        else:
            text_width = max(320, int(content_width * 0.85))
        wrap = min(text_width, content_width - 120)
        for label in self._wrap_labels:
            try:
                label.configure(wraplength=wrap)
            except Exception:
                continue

    def on_show(self):
        if self._reveal_job is not None:
            try:
                self.after_cancel(self._reveal_job)
            except Exception:
                pass
        for label in self._bullet_labels:
            try:
                label.grid_remove()
            except Exception:
                continue
        self._reveal_index = 0
        self._reveal_next()

    def on_hide(self):
        if self._reveal_job is not None:
            try:
                self.after_cancel(self._reveal_job)
            except Exception:
                pass
            self._reveal_job = None

    def _reveal_next(self):
        if not self.winfo_exists():
            return
        if self._reveal_index >= len(self._bullet_labels):
            return
        label = self._bullet_labels[self._reveal_index]
        try:
            label.grid()
        except Exception:
            return
        self._reveal_index += 1
        self._reveal_job = self.after(120, self._reveal_next)


class WelcomeView(_BaseOnboardingView):
    def __init__(self, app, parent):
        hero = app.hero_image or app.brand_image
        super().__init__(
            app,
            parent,
            STRINGS["welcome_title"],
            STRINGS["welcome_subtitle"],
            STRINGS["welcome_bullets"],
            STRINGS["welcome_cta"],
            app.show_tutorial,
            hero_image=hero,
        )


class TutorialView(_BaseOnboardingView):
    def __init__(self, app, parent):
        super().__init__(
            app,
            parent,
            STRINGS["tutorial_title"],
            STRINGS["tutorial_subtitle"],
            STRINGS["tutorial_steps"],
            STRINGS["tutorial_cta"],
            app.show_panel,
        )


def _blend_hex(start, end, t):
    start = start.lstrip("#")
    end = end.lstrip("#")
    r1, g1, b1 = int(start[0:2], 16), int(start[2:4], 16), int(start[4:6], 16)
    r2, g2, b2 = int(end[0:2], 16), int(end[2:4], 16), int(end[4:6], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"
