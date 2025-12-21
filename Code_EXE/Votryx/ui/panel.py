"""Modular control panel UI for VOTRYX."""

import tkinter as tk
from tkinter import scrolledtext, ttk

from ui.strings import STRINGS


class ControlPanelView(ttk.Frame):
    """Primary control panel view."""

    def __init__(self, app, parent):
        super().__init__(parent, style="Main.TFrame", padding=16)
        self.app = app
        self.colors = app.colors
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0, minsize=80)
        self.rowconfigure(1, weight=0, minsize=120)
        self.rowconfigure(2, weight=1, minsize=320)
        self.rowconfigure(3, weight=0, minsize=80)

        header = ttk.Frame(self, style="Main.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(1, weight=1)

        title = ttk.Label(header, text=STRINGS["header_title"], style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")
        subtitle = ttk.Label(
            header,
            text=STRINGS["header_subtitle"],
            foreground=self.colors["muted"],
            background=self.colors["bg"],
            font=("Bahnschrift", 10),
        )
        subtitle.grid(row=1, column=0, sticky="w")

        self.app.state_badge = tk.Label(
            header,
            text=STRINGS["state_idle"],
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Bahnschrift SemiBold", 11),
            padx=12,
            pady=6,
        )
        self.app.state_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        stats_wrapper = ttk.LabelFrame(
            self, text=STRINGS["section_status"], style="Panel.TFrame", padding=10
        )
        stats_wrapper.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        stats_wrapper.columnconfigure(0, weight=1)
        stats_wrapper.rowconfigure(0, weight=1)
        self.app.stats_wrapper = stats_wrapper

        stats_frame = ttk.Frame(stats_wrapper, style="Panel.TFrame")
        stats_frame.grid(row=0, column=0, sticky="nsew")
        for idx in range(self.app.STAT_CARDS_COUNT):
            stats_frame.columnconfigure(idx, weight=1, minsize=180)
        stats_frame.rowconfigure(0, weight=1)

        self.app._make_stat_card(stats_frame, 0, 0, STRINGS["stat_votes"], "0", "count")
        self.app._make_stat_card(stats_frame, 0, 1, STRINGS["stat_errors"], "0", "errors")
        self.app._make_stat_card(
            stats_frame, 0, 2, STRINGS["stat_state"], STRINGS["state_idle"], "status"
        )
        self.app._make_stat_card(stats_frame, 0, 3, STRINGS["stat_runtime"], "00:00:00", "runtime")

        settings_frame = ttk.LabelFrame(
            self, text=STRINGS["section_settings"], style="Panel.TFrame", padding=12
        )
        settings_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 10))
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.rowconfigure(1, weight=1)
        self.app.settings_frame = settings_frame

        general_block = ttk.LabelFrame(
            settings_frame, text=STRINGS["section_general"], style="Panel.TFrame", padding=10
        )
        general_block.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        general_block.columnconfigure(1, weight=1)

        ttk.Label(
            general_block,
            text=STRINGS["label_target_url"],
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=0, column=0, sticky="w", pady=(4, 0), padx=(0, 8))
        self.app.url_entry = ttk.Entry(general_block)
        self.app.url_entry.insert(0, self.app.target_url)
        self.app.url_entry.grid(row=0, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(
            general_block,
            text=STRINGS["helper_target_url"],
            style="Helper.TLabel",
            wraplength=420,
        ).grid(row=1, column=1, sticky="w", pady=(2, 8))

        grid = ttk.Frame(general_block, style="Panel.TFrame")
        grid.grid(row=2, column=0, columnspan=2, sticky="ew")
        grid.columnconfigure((0, 2), weight=0)
        grid.columnconfigure((1, 3), weight=1)

        def add_field(row_idx, col_base, label_text, default_value, helper_text):
            ttk.Label(
                grid,
                text=label_text,
                background=self.colors["panel"],
                foreground=self.colors["text"],
            ).grid(row=row_idx * 2, column=col_base, sticky="w", pady=(8, 0), padx=(0, 10))
            entry = ttk.Entry(grid, width=12)
            entry.insert(0, str(default_value))
            entry.grid(row=row_idx * 2, column=col_base + 1, sticky="ew", pady=(8, 0))
            ttk.Label(grid, text=helper_text, style="Helper.TLabel", wraplength=200).grid(
                row=row_idx * 2 + 1, column=col_base + 1, sticky="w", pady=(2, 8)
            )
            return entry

        self.app.pause_entry = add_field(
            0,
            0,
            STRINGS["label_vote_interval"],
            self.app.pause_between_votes,
            STRINGS["helper_vote_interval"],
        )
        self.app.batch_entry = add_field(
            0,
            2,
            STRINGS["label_batch_size"],
            self.app.batch_size,
            STRINGS["helper_batch_size"],
        )
        self.app.timeout_entry = add_field(
            1,
            0,
            STRINGS["label_timeout"],
            self.app.timeout_seconds,
            STRINGS["helper_timeout"],
        )
        self.app.max_errors_entry = add_field(
            1,
            2,
            STRINGS["label_max_errors"],
            self.app.max_errors,
            STRINGS["helper_max_errors"],
        )
        self.app.backoff_entry = add_field(
            2,
            0,
            STRINGS["label_backoff"],
            self.app.backoff_seconds,
            STRINGS["helper_backoff"],
        )
        self.app.backoff_cap_entry = add_field(
            2,
            2,
            STRINGS["label_backoff_cap"],
            self.app.backoff_cap_seconds,
            STRINGS["helper_backoff_cap"],
        )
        self.app.parallel_entry = add_field(
            3,
            0,
            STRINGS["label_parallel"],
            self.app.parallel_workers,
            STRINGS["helper_parallel"],
        )

        toggles = ttk.Frame(general_block, style="Panel.TFrame")
        toggles.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        toggles.columnconfigure((0, 1), weight=1)
        self.app.headless_var = tk.BooleanVar(value=self.app.headless)
        self.app.headless_check = ttk.Checkbutton(
            toggles,
            text=STRINGS["toggle_headless"],
            variable=self.app.headless_var,
            style="Switch.TCheckbutton",
        )
        self.app.headless_check.grid(row=0, column=0, sticky="w", padx=(0, 16), pady=(0, 4))
        self.app.auto_driver_var = tk.BooleanVar(value=self.app.use_selenium_manager)
        self.app.auto_driver_check = ttk.Checkbutton(
            toggles,
            text=STRINGS["toggle_auto_driver"],
            variable=self.app.auto_driver_var,
            style="Switch.TCheckbutton",
        )
        self.app.auto_driver_check.grid(row=0, column=1, sticky="w", pady=(0, 4))
        ttk.Label(
            toggles,
            text=STRINGS["helper_headless"],
            style="Helper.TLabel",
            wraplength=420,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        advanced_block = ttk.LabelFrame(
            settings_frame, text=STRINGS["section_advanced"], style="Panel.TFrame", padding=10
        )
        advanced_block.grid(row=1, column=0, sticky="nsew")
        advanced_block.columnconfigure(1, weight=1)
        self.app.advanced_tab = advanced_block
        self.app.general_tab = general_block

        self.app.random_ua_check = ttk.Checkbutton(
            advanced_block,
            text=STRINGS["toggle_random_ua"],
            variable=self.app.random_ua_var,
            style="Switch.TCheckbutton",
        )
        self.app.random_ua_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 2))
        ttk.Label(
            advanced_block,
            text=STRINGS["helper_random_ua"],
            style="Helper.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.app.block_images_check = ttk.Checkbutton(
            advanced_block,
            text=STRINGS["toggle_block_images"],
            variable=self.app.block_images_var,
            style="Switch.TCheckbutton",
        )
        self.app.block_images_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))
        ttk.Label(
            advanced_block,
            text=STRINGS["helper_block_images"],
            style="Helper.TLabel",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(
            advanced_block,
            text=STRINGS["label_user_agents"],
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=4, column=0, sticky="nw", pady=(4, 0), padx=(0, 8))
        self.app.ua_text = scrolledtext.ScrolledText(
            advanced_block,
            height=4,
            width=36,
            background=self.colors["panel"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Cascadia Mono", 9),
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["card"],
        )
        self.app.ua_text.grid(row=4, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(advanced_block, text=STRINGS["helper_user_agents"], style="Helper.TLabel").grid(
            row=5, column=1, sticky="w", pady=(0, 8)
        )
        for line in self.app.custom_user_agents:
            self.app.ua_text.insert(tk.END, f"{line}\n")

        ttk.Label(
            advanced_block,
            text=STRINGS["label_vote_selectors"],
            background=self.colors["panel"],
            foreground=self.colors["text"],
        ).grid(row=6, column=0, sticky="nw", pady=(4, 0), padx=(0, 8))
        self.app.selectors_text = scrolledtext.ScrolledText(
            advanced_block,
            height=4,
            width=36,
            background=self.colors["panel"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Cascadia Mono", 9),
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["card"],
        )
        self.app.selectors_text.grid(row=6, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(
            advanced_block,
            text=STRINGS["helper_vote_selectors"],
            style="Helper.TLabel",
        ).grid(row=7, column=1, sticky="w", pady=(0, 8))
        for line in self.app.config.get("vote_selectors", []):
            self.app.selectors_text.insert(tk.END, f"{line}\n")

        actions = ttk.Frame(settings_frame, style="Panel.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        actions.columnconfigure((0, 1), weight=1)
        self.app.apply_btn = ttk.Button(
            actions,
            text=STRINGS["button_apply"],
            command=self.app.apply_settings,
            style="Ghost.TButton",
        )
        self.app.apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=3)
        self.app.defaults_btn = ttk.Button(
            actions,
            text=STRINGS["button_defaults"],
            command=self.app.reset_to_defaults,
            style="Ghost.TButton",
        )
        self.app.defaults_btn.grid(row=0, column=1, sticky="ew", ipady=3)

        log_frame = ttk.LabelFrame(
            self, text=STRINGS["section_log"], style="Panel.TFrame", padding=12
        )
        log_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 10))
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.app.log_frame = log_frame

        log_controls = ttk.Frame(log_frame, style="Panel.TFrame")
        log_controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        log_controls.columnconfigure(2, weight=1)
        self.app.success_badge = tk.Label(
            log_controls,
            text=f"{STRINGS['badge_success']}: 0",
            bg=self.colors["success"],
            fg="#0f172a",
            font=("Bahnschrift SemiBold", 9),
            padx=8,
            pady=4,
        )
        self.app.success_badge.grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.app.failure_badge = tk.Label(
            log_controls,
            text=f"{STRINGS['badge_errors']}: 0",
            bg=self.colors["error"],
            fg="#0f172a",
            font=("Bahnschrift SemiBold", 9),
            padx=8,
            pady=4,
        )
        self.app.failure_badge.grid(row=0, column=1, padx=(0, 12), sticky="w")
        auto_check = ttk.Checkbutton(
            log_controls,
            text=STRINGS["toggle_autoscroll"],
            variable=self.app.autoscroll_var,
            style="Switch.TCheckbutton",
            command=self.app._render_log,
        )
        auto_check.grid(row=0, column=2, sticky="e", padx=(0, 6))
        error_check = ttk.Checkbutton(
            log_controls,
            text=STRINGS["toggle_errors_only"],
            variable=self.app.errors_only_var,
            style="Switch.TCheckbutton",
            command=self.app.toggle_errors_only,
        )
        error_check.grid(row=0, column=3, sticky="e")

        self.app.log_area = scrolledtext.ScrolledText(
            log_frame,
            width=60,
            height=18,
            background=self.colors["bg"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Cascadia Mono", 10),
            borderwidth=1,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.colors["card"],
        )
        self.app.log_area.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        self.app.log_area.tag_configure("info", foreground=self.colors["text"])
        self.app.log_area.tag_configure("success", foreground=self.colors["success"])
        self.app.log_area.tag_configure("error", foreground=self.colors["error"])
        self.app.log_area.tag_configure("muted", foreground=self.colors["muted"])
        clear_btn = ttk.Button(
            log_frame,
            text=STRINGS["button_clear_log"],
            command=self.app.clear_log,
            style="Ghost.TButton",
        )
        clear_btn.grid(row=2, column=0, sticky="e")

        actions_frame = ttk.LabelFrame(
            self, text=STRINGS["section_actions"], style="Panel.TFrame", padding=12
        )
        actions_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        actions_frame.columnconfigure(0, weight=1)
        self.app.actions_frame = actions_frame

        controls = ttk.Frame(actions_frame, style="Panel.TFrame")
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.app.start_btn = ttk.Button(
            controls,
            text=STRINGS["button_start"],
            command=self.app.start_bot,
            style="Accent.TButton",
        )
        self.app.start_btn.grid(row=0, column=0, padx=6, pady=6, sticky="ew", ipady=4)
        self.app.stop_btn = ttk.Button(
            controls,
            text=STRINGS["button_stop"],
            command=self.app.stop_bot,
            style="Ghost.TButton",
            state=tk.DISABLED,
        )
        self.app.stop_btn.grid(row=0, column=1, padx=6, pady=6, sticky="ew", ipady=4)
        self.app.preflight_btn = ttk.Button(
            controls,
            text=STRINGS["button_preflight"],
            command=self.app.run_preflight,
            style="Ghost.TButton",
        )
        self.app.preflight_btn.grid(row=0, column=2, padx=6, pady=6, sticky="ew", ipady=4)
        self.app.logs_btn = ttk.Button(
            controls,
            text=STRINGS["button_open_logs"],
            command=self.app.open_logs,
            style="Ghost.TButton",
        )
        self.app.logs_btn.grid(row=0, column=3, padx=6, pady=6, sticky="ew", ipady=4)
        self.app.reset_btn = ttk.Button(
            controls,
            text=STRINGS["button_reset_counters"],
            command=self.app.reset_counters,
            style="Ghost.TButton",
        )
        self.app.reset_btn.grid(row=0, column=4, padx=6, pady=6, sticky="ew", ipady=4)

        if getattr(self.app, "tray_available", False):
            self.app.tray_btn = ttk.Button(
                controls,
                text=STRINGS["button_tray"],
                command=self.app._minimize_to_tray,
                style="Outline.TButton",
            )
            self.app.tray_btn.grid(row=0, column=5, padx=6, pady=6, sticky="ew", ipady=4)
