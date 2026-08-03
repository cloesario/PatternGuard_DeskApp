import os
import time
import threading
import tkinter as tk
import cv2
import numpy as np
from tkinter import ttk, filedialog, messagebox
from evaluation_metrics import calculate_restoration_metrics
from PIL import Image, ImageTk, ImageOps
from cultural_data import SUBCLASS_DATA
from dsp_engine import (
    run_algorithm_i_autocorrelation,
    run_algorithm_ii_defect_isolation,
    run_algorithm_iii_template_alignment,
)

class PatternGuardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PatternGuard Desktop")
        self.geometry("1280x880")
        self.minsize(1200, 840)
        self.configure_styles()

        # State Variables
        self.uploaded_file_path = None
        self.original_bgr = None
        self.original_image_pil = None
        self.tracking_pattern_pil = None
        self.heatmap_hires = None
        self.reconstructed_image_pil = None
        self.reconstructed_image_hires = None
        self.img_tk_cache = {}
        self.active_subclass_id = "concha_concha"

        self.create_layout()
        self.on_subclass_changed(None)

    def configure_styles(self):
        self.colors = {
            "bg": "#F4EFEA",
            "card": "#FFFFFF",
            "border": "#E3DCD6",
            "text_primary": "#1D265C",
            "text_dark": "#2E2E30",
            "text_grey": "#6E6E73",
            "maroon": "#8C2D2D",
            "maroon_hover": "#A63A3A",
            "navy_btn": "#1D265C",
            "navy_btn_hover": "#2B3882",
            "gold": "#D97706",
            "banner_bg": "#E8EAF6",
            "banner_border": "#3F51B5",
            "emerald": "#10B981"
        }
        self.configure(bg=self.colors["bg"])
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TCombobox",
                             fieldbackground="#FFFFFF",
                             background="#FFFFFF",
                             foreground=self.colors["text_dark"],
                             bordercolor=self.colors["border"],
                             lightcolor=self.colors["border"],
                             darkcolor=self.colors["border"])

    def create_layout(self):
        # HEADER BAR
        header_bar = tk.Frame(self, bg="#FFFFFF", height=75, bd=0, relief="flat")
        header_bar.pack(fill="x", side="top")
        header_bar.pack_propagate(False)

        logo_frame = tk.Frame(header_bar, bg="#FAF6F0", highlightbackground=self.colors["maroon"], highlightthickness=1, bd=0)
        logo_frame.pack(side="left", padx=(25, 12), pady=12)
        logo_lbl = tk.Label(logo_frame, text="◆  ◆  ◆", bg="#FAF6F0", fg=self.colors["maroon"], font=("Segoe UI", 10, "bold"), padx=10, pady=2)
        logo_lbl.pack()

        brand_frame = tk.Frame(header_bar, bg="#FFFFFF")
        brand_frame.pack(side="left", fill="y", pady=12)
        title_lbl = tk.Label(brand_frame, text="PATTERNGUARD", bg="#FFFFFF", fg=self.colors["text_primary"], font=("Segoe UI", 16, "bold"))
        title_lbl.pack(anchor="w")
        sub_title_lbl = tk.Label(brand_frame, text="FILIPINO TEXTILE AUDITING & RESTORATION FRAMEWORK", bg="#FFFFFF", fg=self.colors["maroon"], font=("Segoe UI", 7, "bold"))
        sub_title_lbl.pack(anchor="w", pady=(2, 0))

        sep = tk.Frame(self, bg=self.colors["border"], height=1)
        sep.pack(fill="x", side="top")

        # MAIN WORKSPACE
        workspace_wrapper = tk.Frame(self, bg=self.colors["bg"])
        workspace_wrapper.pack(fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(workspace_wrapper, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(workspace_wrapper, bg=self.colors["bg"], bd=0, highlightthickness=0, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        main_container = tk.Frame(self.canvas, bg=self.colors["bg"])
        self.canvas_frame_id = self.canvas.create_window((0, 0), window=main_container, anchor="nw")

        main_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_frame_id, width=e.width))

        left_col = tk.Frame(main_container, bg=self.colors["bg"], width=380)
        left_col.pack(side="left", fill="both", padx=(25, 0), pady=20)
        left_col.pack_propagate(False)

        right_col = tk.Frame(main_container, bg=self.colors["bg"])
        right_col.pack(side="left", fill="both", expand=True, padx=(25, 25), pady=20)

        self.build_left_column(left_col)
        self.build_right_column(right_col)

    def build_left_column(self, parent):
        self.card_input = self.create_card(parent, "Input & Verify", "📸")
        self.card_input.pack(fill="x", pady=(0, 20))

        self.upload_container = tk.Frame(self.card_input, bg="#FFFFFF")
        self.upload_container.pack(fill="x", padx=15, pady=(5, 15))

        self.upload_canvas = tk.Canvas(self.upload_container, height=155, bg="#FFFFFF", bd=0, highlightthickness=0, cursor="hand2")
        self.upload_canvas.pack(fill="x")
        self.upload_canvas.bind("<Button-1>", lambda e: self.trigger_file_upload())
        self.draw_upload_slot()

        self.uploaded_state_frame = tk.Frame(self.upload_container, bg="#FFFFFF")
        self.file_row = tk.Frame(self.uploaded_state_frame, bg="#FFFFFF", highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        self.file_row.pack(fill="x", pady=(0, 12))

        self.file_name_lbl = tk.Label(self.file_row, text="No file selected", bg="#FFFFFF", fg=self.colors["text_dark"], font=("Segoe UI", 10, "bold"), anchor="w")
        self.file_name_lbl.pack(side="left", padx=12, pady=10, fill="x", expand=True)

        self.re_upload_btn = tk.Button(self.file_row, text="Re-Upload", bg="#FFFFFF", fg=self.colors["maroon"],
                                       activebackground="#FAF2EE", activeforeground=self.colors["maroon"],
                                       font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                                       highlightbackground=self.colors["maroon"], highlightthickness=1,
                                       command=self.trigger_file_upload, cursor="hand2")
        self.re_upload_btn.pack(side="right", padx=10, pady=6)

        self.banner_frame = tk.Frame(self.uploaded_state_frame, bg=self.colors["banner_bg"], highlightbackground=self.colors["banner_border"], highlightthickness=1, bd=0)
        self.banner_frame.pack(fill="x")
        self.banner_frame.columnconfigure(1, weight=1)

        check_lbl = tk.Label(self.banner_frame, text="✓", bg=self.colors["banner_bg"], fg=self.colors["banner_border"], font=("Segoe UI", 14, "bold"))
        check_lbl.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="n")

        banner_text = "Verification Success: Image input ready for Wiener-Khinchin FFT lattice extraction."
        self.banner_msg_lbl = tk.Label(self.banner_frame, text=banner_text, bg=self.colors["banner_bg"], fg=self.colors["banner_border"], font=("Segoe UI", 9, "bold"), wraplength=270, justify="left")
        self.banner_msg_lbl.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="w")

        # Config Card
        self.card_config = self.create_card(parent, "Configuration", "⚙️")
        self.card_config.pack(fill="x")

        config_inner = tk.Frame(self.card_config, bg="#FFFFFF")
        config_inner.pack(fill="x", padx=15, pady=(5, 15))

        lbl_cat = tk.Label(config_inner, text="TEXTILE CATEGORY", bg="#FFFFFF", fg=self.colors["text_grey"], font=("Segoe UI", 8, "bold"))
        lbl_cat.pack(anchor="w", pady=(0, 4))

        categories = sorted({v["category"] for v in SUBCLASS_DATA.values()})
        self.category_box = ttk.Combobox(config_inner, values=categories, state="readonly", font=("Segoe UI", 10))
        self.category_box.pack(fill="x", pady=(0, 15))
        self.category_box.bind("<<ComboboxSelected>>", self.on_category_changed)

        lbl_sub = tk.Label(config_inner, text="SUBCLASS", bg="#FFFFFF", fg=self.colors["text_grey"], font=("Segoe UI", 8, "bold"))
        lbl_sub.pack(anchor="w", pady=(0, 4))

        self.subclass_box = ttk.Combobox(config_inner, state="readonly", font=("Segoe UI", 10))
        self.subclass_box["values"] = []
        self.subclass_box.set("")
        self.subclass_box.pack(fill="x", pady=(0, 20))
        self.subclass_box.bind("<<ComboboxSelected>>", self.on_subclass_changed)

        btn_row = tk.Frame(config_inner, bg="#FFFFFF")
        btn_row.pack(fill="x", pady=5)

        self.reconstruct_btn = self.create_flat_button(
            btn_row, text="Run Pipeline", bg=self.colors["maroon"], fg="#FFFFFF",
            hover_bg=self.colors["maroon_hover"], command=self.run_reconstruction_pipeline,
            font=("Segoe UI", 10, "bold"), height=38
        )
        self.reconstruct_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.rerun_pipeline_btn = self.create_flat_button(
            btn_row, text="🔄 RE-RUN", bg=self.colors["navy_btn"], fg="#FFFFFF",
            hover_bg=self.colors["navy_btn_hover"], command=self.run_reconstruction_pipeline,
            font=("Segoe UI", 10, "bold"), height=38
        )
        self.rerun_pipeline_btn.pack(side="left", fill="x", padx=(5, 0))

        # DESCRIPTION CARD
        self.card_description = self.create_card(parent, "Description", "📝")
        self.card_description.pack(fill="x", pady=(12, 20))

        desc_inner = tk.Frame(self.card_description, bg="#FFFFFF")
        desc_inner.pack(fill="x", padx=15, pady=(8, 12))

        self.description_text = tk.Text(desc_inner, bg="#FFFFFF", fg=self.colors["text_dark"], font=("Segoe UI", 10, "italic"), wrap="word", relief="flat", bd=0, height=4, highlightthickness=0)
        self.description_text.pack(fill="x")
        self.description_text.insert("1.0", "Waiting for configuration")
        self.description_text.configure(state="disabled")

    def draw_upload_slot(self):
        self.upload_canvas.delete("all")
        self.upload_canvas.create_rectangle(2, 2, 344, 152, outline=self.colors["border"], width=1.5, dash=(6, 4))
        self.upload_canvas.create_polygon(158, 40, 172, 40, 176, 46, 198, 46, 198, 70, 158, 70, fill="#E8EAF6", outline="#3F51B5", width=2)
        self.upload_canvas.create_line(178, 65, 178, 48, arrow=tk.FIRST, fill="#EF4444", width=3)
        self.upload_canvas.create_text(178, 98, text="Upload Textile Image", font=("Segoe UI", 11, "bold"), fill=self.colors["text_primary"])
        self.upload_canvas.create_text(178, 120, text="PNG, JPG up to 10MB", font=("Segoe UI", 9), fill=self.colors["text_grey"])

    def build_right_column(self, parent):
        self.card_visuals = self.create_card(parent, "Visual Results & Comparisons", "📊")
        self.card_visuals.pack(fill="x", pady=(0, 20))

        visuals_inner = tk.Frame(self.card_visuals, bg="#FFFFFF")
        visuals_inner.pack(fill="x", padx=15, pady=(5, 15))
        visuals_inner.columnconfigure(0, weight=1)
        visuals_inner.columnconfigure(1, weight=1)
        visuals_inner.columnconfigure(2, weight=1)

        self.panel_orig = self.create_image_panel(visuals_inner, 0, "ORIGINAL IMAGE")
        self.panel_track = self.create_image_panel(visuals_inner, 1, "DETECTED ERROR HEATMAP")
        self.panel_recon = self.create_image_panel(visuals_inner, 2, "RECONSTRUCTED TEXTILE")

        # Buttons row below panels - aligned to match panel width
        buttons_inner = tk.Frame(self.card_visuals, bg="#FFFFFF")
        buttons_inner.pack(fill="x", padx=15, pady=(0, 15))
        buttons_inner.columnconfigure(0, weight=1)
        buttons_inner.columnconfigure(1, weight=1)
        buttons_inner.columnconfigure(2, weight=1)

        # Heatmap export button
        self.export_heatmap_btn = self.create_flat_button(
            buttons_inner, text="📦 Export Heatmap", bg=self.colors["navy_btn"], fg="#FFFFFF",
            hover_bg=self.colors["navy_btn_hover"], command=self.export_heatmap, font=("Segoe UI", 9, "bold"), height=20
        )
        self.export_heatmap_btn.grid(row=0, column=1, padx=8, pady=(10, 0), sticky="ew")
        self.export_heatmap_btn.configure(state="disabled")

        # Reconstruction export button
        self.export_btn = self.create_flat_button(
            buttons_inner, text="📦 Export Reconstruction", bg=self.colors["navy_btn"], fg="#FFFFFF",
            hover_bg=self.colors["navy_btn_hover"], command=self.export_restored_photo, font=("Segoe UI", 9, "bold"), height=20
        )
        self.export_btn.grid(row=0, column=2, padx=8, pady=(10, 0), sticky="ew")
        self.export_btn.configure(state="disabled")

        metrics_container = tk.Frame(parent, bg=self.colors["bg"])
        metrics_container.pack(fill="x", pady=(0, 20))
        metrics_container.columnconfigure(0, weight=1)
        metrics_container.columnconfigure(1, weight=1)

        self.card_confidence = self.create_card(metrics_container, "SYSTEM CONFIDENCE METRICS", "", has_border=True)
        self.card_confidence.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        conf_inner = tk.Frame(self.card_confidence, bg="#FFFFFF")
        conf_inner.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self.group_lbl = tk.Label(conf_inner, text="Wallpaper Group: Waiting for configuration", bg="#FFFFFF", fg=self.colors["text_primary"], font=("Segoe UI", 11, "italic", "bold"), cursor="hand2")
        self.group_lbl.pack(anchor="w", pady=(0, 10))
        self.group_lbl.bind("<Button-1>", lambda e: self.show_wallpaper_guide_window())
        
        self.guide_window = None

        self.progress_canvas = tk.Canvas(conf_inner, height=10, bg="#E3DCD6", bd=0, highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=(0, 15))
        self.draw_progress_bar(0)

        stats_row = tk.Frame(conf_inner, bg="#FFFFFF")
        stats_row.pack(fill="x")
        stats_row.columnconfigure(0, weight=1)
        stats_row.columnconfigure(1, weight=1)
        stats_row.columnconfigure(2, weight=1)

        self.box_acc = self.create_stat_box(stats_row, 0, "Accuracy")
        self.box_rec = self.create_stat_box(stats_row, 1, "A1 Lattice")
        self.box_f1 = self.create_stat_box(stats_row, 2, "A2 Lattice")

        self.card_sfs = self.create_card(metrics_container, "SYMMETRY FIDELITY SCORE (%)", "", has_border=True)
        self.card_sfs.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        sfs_inner = tk.Frame(self.card_sfs, bg="#FFFFFF")
        sfs_inner.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        sfs_header_row = tk.Frame(sfs_inner, bg="#FFFFFF")
        sfs_header_row.pack(fill="x", pady=(0, 10))

        self.sfs_num_lbl = tk.Label(sfs_header_row, text="--", bg="#FFFFFF", fg=self.colors["text_grey"], font=("Segoe UI", 28, "bold"))
        self.sfs_num_lbl.pack(side="left")

        threshold_lbl = tk.Label(sfs_header_row, text="(Threshold: 95%)", bg="#FFFFFF", fg=self.colors["text_grey"], font=("Segoe UI", 10))
        threshold_lbl.pack(side="left", padx=(10, 0), pady=(15, 0))

        grid_frame = tk.Frame(sfs_inner, bg="#FFFFFF")
        grid_frame.pack(fill="x", pady=(0, 15))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        self.grid_acc = self.create_grid_cell(grid_frame, 0, 0, "Accuracy", "--")
        self.grid_rec = self.create_grid_cell(grid_frame, 0, 1, "Recall", "--")
        self.grid_fpr = self.create_grid_cell(grid_frame, 1, 0, "False Positive Rate", "--")
        self.grid_iou = self.create_grid_cell(grid_frame, 1, 1, "Intersection over Union", "--")

        self.rerun_btn = self.create_flat_border_button(
            sfs_inner, text="⚡ RUN OPTIMIZATION PIPELINE", bg="#FFFFFF", fg=self.colors["text_primary"],
            hover_bg="#F0F4FF", border_color=self.colors["text_primary"], command=self.run_optimization_pipeline
        )
        self.rerun_btn.pack(fill="x")
        self.rerun_btn.configure(state="disabled")

        # Context Card
        self.card_context = tk.Frame(parent, bg="#FAF6F0", highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        self.card_context.pack(fill="x")

        gold_accent_bar = tk.Frame(self.card_context, bg=self.colors["gold"], width=4)
        gold_accent_bar.pack(side="left", fill="y")

        context_inner = tk.Frame(self.card_context, bg="#FAF6F0")
        context_inner.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        context_title = tk.Label(context_inner, text="📜  Traditional Context & Cultural Origin", bg="#FAF6F0", fg=self.colors["text_primary"], font=("Segoe UI", 11, "bold"))
        context_title.pack(anchor="w", pady=(0, 5))

        cultural_label = tk.Label(context_inner, text="Cultural Background:", bg="#FAF6F0", fg=self.colors["text_primary"], font=("Segoe UI", 9, "bold"))
        cultural_label.pack(anchor="w", pady=(0, 2))

        self.cultural_text = tk.Text(context_inner, bg="#FAF6F0", fg=self.colors["text_dark"], font=("Segoe UI", 9, "italic"), wrap="word", relief="flat", bd=0, height=3, highlightthickness=0)
        self.cultural_text.pack(fill="x", anchor="w", pady=(0, 8))
        self.cultural_text.insert("1.0", "Waiting for configuration")
        self.cultural_text.configure(state="disabled")

        self.source_lbl = tk.Label(context_inner, text="Source: Waiting for configuration", bg="#FAF6F0", fg=self.colors["text_grey"], font=("Segoe UI", 8))
        self.source_lbl.pack(anchor="w")

    def create_card(self, parent, title_text, icon_prefix="", has_border=True):
        card = tk.Frame(parent, bg="#FFFFFF")
        if has_border:
            card.configure(highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        header_container = tk.Frame(card, bg="#FFFFFF")
        header_container.pack(fill="x")
        card.header_container = header_container
        header_txt = f"{icon_prefix}  {title_text}" if icon_prefix else title_text
        header_lbl = tk.Label(header_container, text=header_txt, bg="#FFFFFF", fg=self.colors["text_primary"], font=("Segoe UI", 12, "bold"), anchor="w")
        header_lbl.pack(side="left", padx=15, pady=(15, 8))
        return card

    def create_image_panel(self, parent, col, label_text):
        frame = tk.Frame(parent, bg="#FFFFFF")
        frame.grid(row=0, column=col, padx=8, sticky="nsew")
        lbl = tk.Label(frame, text=label_text, bg="#FFFFFF", fg=self.colors["text_grey"], font=("Segoe UI", 9, "bold"))
        lbl.pack(anchor="center", pady=(5, 6))
        slot = tk.Frame(frame, bg="#F5F3EF", highlightbackground=self.colors["border"], highlightthickness=1, bd=0, width=280, height=280)
        slot.pack(fill="both", expand=True)
        slot.pack_propagate(False)
        placeholder = tk.Label(slot, text="Awaiting processing" if col > 0 else "No image uploaded", bg="#F5F3EF", fg=self.colors["text_grey"], font=("Segoe UI", 10))
        placeholder.pack(expand=True)
        slot.placeholder = placeholder
        return slot

    def create_stat_box(self, parent, col, name):
        box = tk.Frame(parent, bg="#FAF6F0", highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        box.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        name_lbl = tk.Label(box, text=name, bg="#FAF6F0", fg=self.colors["text_grey"], font=("Segoe UI", 9))
        name_lbl.pack(anchor="center", pady=(8, 2))
        num_lbl = tk.Label(box, text="--", bg="#FAF6F0", fg=self.colors["text_grey"], font=("Segoe UI", 14, "bold"))
        num_lbl.pack(anchor="center", pady=(0, 8))
        box.num_lbl = num_lbl
        return box

    def create_grid_cell(self, parent, row, col, label_text, default_val):
        cell = tk.Frame(parent, bg="#FAF6F0", highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        cell.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        lbl = tk.Label(cell, text=f"{label_text}: ", bg="#FAF6F0", fg=self.colors["text_grey"], font=("Segoe UI", 9))
        lbl.pack(side="left", padx=(10, 2), pady=6)
        val_lbl = tk.Label(cell, text=default_val, bg="#FAF6F0", fg=self.colors["text_dark"], font=("Segoe UI", 10, "bold"))
        val_lbl.pack(side="left")
        cell.val_lbl = val_lbl
        return cell

    def draw_progress_bar(self, percentage):
        self.progress_canvas.delete("all")
        self.progress_canvas.update()
        w = self.progress_canvas.winfo_width()
        if w <= 1:
            w = 340
        self.create_rounded_rect(self.progress_canvas, 0, 0, w, 10, fill="#E3DCD6")
        if percentage > 0:
            fill_w = max(10, int((percentage / 100.0) * w))
            bar_color = self.colors["emerald"] if percentage >= 95 else self.colors["maroon"]
            self.create_rounded_rect(self.progress_canvas, 0, 0, fill_w, 10, fill=bar_color)

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, fill):
        r = y2 - y1
        canvas.create_oval(x1, y1, x1 + r, y2, fill=fill, outline="")
        canvas.create_oval(x2 - r, y1, x2, y2, fill=fill, outline="")
        canvas.create_rectangle(x1 + r / 2, y1, x2 - r / 2, y2, fill=fill, outline="")

    def create_flat_button(self, parent, text, bg, fg, hover_bg, command, font, height):
        btn = tk.Button(parent, text=text, bg=bg, fg=fg, font=font, relief="flat", bd=0,
                        activebackground=hover_bg, activeforeground=fg, command=command, cursor="hand2")
        btn.configure(pady=6)
        return btn

    def create_flat_border_button(self, parent, text, bg, fg, hover_bg, border_color, command):
        btn = tk.Button(parent, text=text, bg=bg, fg=fg, font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                        highlightbackground=border_color, highlightthickness=1,
                        activebackground=hover_bg, activeforeground=fg, command=command, cursor="hand2")
        btn.configure(pady=6)
        return btn

    def on_category_changed(self, event):
        cat = self.category_box.get()
        subclasses = [k for k, v in SUBCLASS_DATA.items() if v["category"] == cat]
        self.subclass_box["values"] = subclasses
        self.subclass_box.set("")

    def on_subclass_changed(self, event):
        sub_id = self.subclass_box.get()
        self.tracking_pattern_pil = None
        self.heatmap_hires = None
        self.reconstructed_image_pil = None
        self.reconstructed_image_hires = None

        if sub_id and sub_id in SUBCLASS_DATA:
            self.active_subclass_id = sub_id
            data = SUBCLASS_DATA[sub_id]
            self.description_text.configure(state="normal")
            self.description_text.delete("1.0", tk.END)
            self.description_text.insert("1.0", data.get("description", ""))
            self.description_text.configure(state="disabled")

            self.cultural_text.configure(state="normal")
            self.cultural_text.delete("1.0", tk.END)
            self.cultural_text.insert("1.0", data.get("Cultural Background", ""))
            self.cultural_text.configure(state="disabled")

            self.group_lbl.configure(text=f"Wallpaper Group: {data.get('group', 'Unknown')}")
            self.source_lbl.configure(text=f"Source: {data.get('source', 'Unknown')}")

    def trigger_file_upload(self):
        file_path = filedialog.askopenfilename(
            title="Upload Textile Image for Auditing",
            filetypes=[("Textile Images", "*.png *.jpg *.jpeg")]
        )
        if not file_path:
            return
        self.uploaded_file_path = file_path
        file_name = os.path.basename(file_path)
        short_name = file_name if len(file_name) < 22 else f"{file_name[:18]}..."
        self.file_name_lbl.configure(text=short_name)
        self.upload_canvas.pack_forget()
        self.uploaded_state_frame.pack(fill="x")
        try:
            self.original_bgr = cv2.imread(file_path)
            pil_img = Image.open(file_path)
            self.original_image_pil = ImageOps.fit(pil_img, (270, 270), Image.Resampling.LANCZOS)
            self.display_pil_in_panel(self.panel_orig, self.original_image_pil, "orig")
        except Exception as e:
            messagebox.showerror("Error Reading Image", f"Failed to open image: {str(e)}")

    def display_pil_in_panel(self, panel_widget, pil_image, cache_key):
        panel_widget.placeholder.pack_forget()
        for child in panel_widget.winfo_children():
            if child != panel_widget.placeholder:
                child.destroy()
        img_tk = ImageTk.PhotoImage(image=pil_image)
        self.img_tk_cache[cache_key] = img_tk
        lbl = tk.Label(panel_widget, image=img_tk, bg="#F5F3EF")
        lbl.pack(fill="both", expand=True)

    def run_reconstruction_pipeline(self):
        if self.original_bgr is None:
            messagebox.showwarning("Image Required", "Please upload a damaged textile image first!")
            return

        self.reconstruct_btn.configure(state="disabled")

        def worker():
            start_time = time.time()
            I_bgr_resized = cv2.resize(self.original_bgr, (256, 256))
            I_gray_eval = cv2.cvtColor(I_bgr_resized, cv2.COLOR_BGR2GRAY)

            R_xx, a1, a2, theta_dom, detected_group = run_algorithm_i_autocorrelation(I_gray_eval)
            M_mask, diff_map = run_algorithm_ii_defect_isolation(I_bgr_resized, a1, a2)

            defect_pixel_count = int((M_mask == 255).sum())
            no_defect_detected = (defect_pixel_count == 0)

            I_final_bgr = run_algorithm_iii_template_alignment(
                I_bgr_resized, M_mask, a1, a2, symmetry_group=detected_group
            )

            runtime_ms = (time.time() - start_time) * 1000
            I_final_gray = cv2.cvtColor(I_final_bgr, cv2.COLOR_BGR2GRAY)

            res = calculate_restoration_metrics(I_gray_eval, I_final_gray, M_mask, None)
            ssim_val, accuracy_val, recall_val, fpr_val, iou_val, sfs_score = res if res else (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

            color_heatmap = cv2.applyColorMap(
                cv2.normalize(diff_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
                cv2.COLORMAP_JET
            )
            color_heatmap[M_mask == 255] = [255, 0, 0]

            heatmap_rgb = cv2.cvtColor(color_heatmap, cv2.COLOR_BGR2RGB)
            final_rgb = cv2.cvtColor(I_final_bgr, cv2.COLOR_BGR2RGB)

            track_pil = Image.fromarray(heatmap_rgb).resize((270, 270), Image.Resampling.LANCZOS)
            recon_pil = Image.fromarray(final_rgb).resize((270, 270), Image.Resampling.LANCZOS)
            recon_hires = Image.fromarray(final_rgb)
            heatmap_hires = Image.fromarray(heatmap_rgb)

            self.after(0, lambda: self.update_pipeline_ui(
                track_pil, recon_pil, recon_hires, heatmap_hires, sfs_score, ssim_val, accuracy_val, recall_val,
                fpr_val, iou_val, a1, a2, theta_dom, detected_group, runtime_ms,
                no_defect_detected=no_defect_detected
            ))

        threading.Thread(target=worker, daemon=True).start()

    def update_pipeline_ui(self, track_pil, recon_pil, recon_hires, heatmap_hires, sfs_score, ssim_val, accuracy_val, recall_val,
                           fpr_val, iou_val, a1, a2, theta_dom, detected_group, runtime_ms,
                           no_defect_detected=False):
        self.reconstruct_btn.configure(state="normal")
        self.tracking_pattern_pil = track_pil
        self.heatmap_hires = heatmap_hires
        self.reconstructed_image_pil = recon_pil
        self.reconstructed_image_hires = recon_hires

        self.display_pil_in_panel(self.panel_track, track_pil, "track")
        self.display_pil_in_panel(self.panel_recon, recon_pil, "recon")

        if detected_group:
            self.group_lbl.configure(text=f"Wallpaper Group: {detected_group}")

        if no_defect_detected:
            self.sfs_num_lbl.configure(text="N/A", fg=self.colors["text_grey"])
            self.draw_progress_bar(0)
        else:
            self.draw_progress_bar(sfs_score)
            self.sfs_num_lbl.configure(
                text=f"{sfs_score:.2f}%",
                fg=self.colors["maroon"] if sfs_score < 95.0 else self.colors["text_primary"]
            )

        self.box_acc.num_lbl.configure(text=f"{accuracy_val:.1f}%", fg=self.colors["text_primary"])
        self.box_rec.num_lbl.configure(text=f"{a1:.1f}", fg=self.colors["text_primary"])
        self.box_f1.num_lbl.configure(text=f"{a2:.1f}", fg=self.colors["text_primary"])

        self.grid_acc.val_lbl.configure(text=f"{accuracy_val:.1f}%")
        self.grid_rec.val_lbl.configure(text=f"{recall_val:.1f}%")
        self.grid_fpr.val_lbl.configure(text=f"{fpr_val:.1f}%")
        self.grid_iou.val_lbl.configure(text=f"{iou_val:.1f}%")

        self.export_btn.configure(state="normal")
        self.export_heatmap_btn.configure(state="normal")
        self.rerun_btn.configure(state="normal")

    def run_optimization_pipeline(self):
        self.run_reconstruction_pipeline()

    def export_restored_photo(self):
        if not self.reconstructed_image_hires:
            messagebox.showwarning("No Image", "Please run the pipeline first!")
            return

        save_path = filedialog.asksaveasfilename(
            title="Export Reconstructed Textile Photo",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")]
        )
        if not save_path:
            return

        try:
            export_image = self.reconstructed_image_hires.resize((500, 500), Image.Resampling.LANCZOS)
            export_image.save(save_path, format="PNG", quality=95)
            messagebox.showinfo("Export Success", f"Reconstructed image saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save file: {str(e)}")

    def export_heatmap(self):
        if not self.heatmap_hires:
            messagebox.showwarning("No Image", "Please run the pipeline first!")
            return

        save_path = filedialog.asksaveasfilename(
            title="Export Error Heatmap",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")]
        )
        if not save_path:
            return

        try:
            export_image = self.heatmap_hires.resize((500, 500), Image.Resampling.LANCZOS)
            export_image.save(save_path, format="PNG", quality=95)
            messagebox.showinfo("Export Success", f"Heatmap saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save file: {str(e)}")

    def show_wallpaper_guide_window(self):
        guide_path = os.path.join(os.path.dirname(__file__), "assets", "wallpaper_group_guide.png")
        
        if not os.path.exists(guide_path):
            messagebox.showwarning("Guide Not Found", "Wallpaper group guide image not found!")
            return
        
        # Close existing window if open
        if self.guide_window is not None and self.guide_window.winfo_exists():
            self.guide_window.destroy()
        
        # Create new window
        self.guide_window = tk.Toplevel(self)
        self.guide_window.title("Wallpaper Group Classification Guide")
        self.guide_window.geometry("600x750")
        self.guide_window.configure(bg=self.colors["bg"])
        
        # Position window below and to the right of main window
        self.guide_window.geometry(f"+{self.winfo_x() + 100}+{self.winfo_y() + 200}")
        
        # Header frame
        header_frame = tk.Frame(self.guide_window, bg=self.colors["navy_btn"])

        
        header_label = tk.Label(
            header_frame, 
            text="Wallpaper Group Classification", 
            bg=self.colors["navy_btn"], 
            fg="#FFFFFF",
            font=("Segoe UI", 12, "bold"),
            padx=15,
            pady=10
        )
        header_label.pack(side="left", fill="x", expand=True)
        
        close_btn = tk.Button(
            header_frame,
            text="✕",
            bg=self.colors["navy_btn"],
            fg="#FFFFFF",
            font=("Segoe UI", 14, "bold"),
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            command=lambda: self.close_wallpaper_window(),
            cursor="hand2",
            activebackground="#0D1541"
        )
        close_btn.pack(side="right", padx=10, pady=5)
        
        # Image display area
        try:
            guide_img = Image.open(guide_path)
            # Scale to fit window
            img_width = 580
            ratio = img_width / guide_img.width
            img_height = int(guide_img.height * ratio)
            guide_img_resized = guide_img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            
            guide_tk = ImageTk.PhotoImage(guide_img_resized)
            
            img_label = tk.Label(self.guide_window, image=guide_tk, bg=self.colors["bg"])
            img_label.image = guide_tk
            img_label.pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load guide image: {str(e)}")
            self.guide_window.destroy()
            self.guide_window = None
    
    def close_wallpaper_window(self):
        if self.guide_window is not None and self.guide_window.winfo_exists():
            self.guide_window.destroy()
            self.guide_window = None

if __name__ == "__main__":
    app = PatternGuardApp()
    app.mainloop()