import json
import subprocess
import sys
from pathlib import Path

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox


ATLASES = [
    "allen_mouse_25um",
    "allen_mouse_10um",
    "whs_sd_rat_39um",
    "swc_female_rat_50um",
]

SHADER_STYLES = ["plastic", "cartoon", "flat", "glossy", "shiny"]

DEFAULT_REGIONS = [
    {"name": "ILA", "color": "darkgreen", "alpha": 0.5},
    {"name": "CA", "color": "salmon", "alpha": 0.5},
    {"name": "DG", "color": "salmon", "alpha": 0.5},
    {"name": "CP", "color": "skyblue", "alpha": 0.5},
    {"name": "PL", "color": "gold", "alpha": 0.5},
    {"name": "BLA", "color": "purple", "alpha": 0.5},
]

DEFAULT_ELECTRODES = [
    {"name": "shank1", "tip": [7200, 1200, 8100], "direction": [0.0153, 0.9999, 0.0], "depth": 4900.57, "color": "black", "linewidth": 10},
    {"name": "shank2", "tip": [7000, 1200, 8400], "direction": [0.0153, 0.9999, 0.0], "depth": 4900.57, "color": "black", "linewidth": 10},
    {"name": "shank3", "tip": [6800, 1200, 8700], "direction": [0.0153, 0.9999, 0.0], "depth": 4900.57, "color": "black", "linewidth": 10},
    {"name": "shank4", "tip": [6600, 1200, 9000], "direction": [0.0153, 0.9999, 0.0], "depth": 4900.57, "color": "black", "linewidth": 10},
    {"name": "shank5", "tip": [3200, 1200, 5300], "direction": [0.0812, 0.9948, -0.0609], "depth": 4925.44, "color": "black", "linewidth": 10},
    {"name": "shank6", "tip": [3500, 1200, 5000], "direction": [0.0812, 0.9948, -0.0609], "depth": 4925.44, "color": "black", "linewidth": 10},
    {"name": "shank7", "tip": [3800, 1200, 4700], "direction": [0.0812, 0.9948, -0.0609], "depth": 4925.44, "color": "black", "linewidth": 10},
    {"name": "shank8", "tip": [4100, 1200, 4400], "direction": [0.0812, 0.9948, -0.0609], "depth": 4925.44, "color": "black", "linewidth": 10},
]


class ColorButton(tk.Canvas):
    def __init__(self, parent, color="black", size=20, command=None, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=1,
                         highlightbackground="gray50", **kwargs)
        self._size = size
        self._color = color
        self._command = command
        self._draw()
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        m = 2
        self.create_rectangle(m, m, self._size - m, self._size - m,
                              fill=self._color, outline="")

    def _on_click(self, _event):
        if self._command:
            self._command()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self._draw()


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas)

        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>",
                        lambda ev: canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
        self.inner.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))


class RegionRow:
    def __init__(self, parent, data, on_delete):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", padx=2, pady=1)

        self.name_var = tk.StringVar(value=data.get("name", ""))
        ttk.Entry(self.frame, textvariable=self.name_var, width=12).pack(side="left", padx=(0, 4))

        self.color_var = tk.StringVar(value=data.get("color", "gray"))
        self.color_btn = ColorButton(self.frame, color=self.color_var.get(),
                                     command=self._pick_color)
        self.color_btn.pack(side="left", padx=(0, 4))

        self.alpha_var = tk.DoubleVar(value=data.get("alpha", 0.5))
        ttk.Spinbox(self.frame, from_=0.0, to=1.0, increment=0.05,
                     textvariable=self.alpha_var, width=5).pack(side="left", padx=(0, 4))

        ttk.Button(self.frame, text="\u2715", width=3,
                   command=lambda: on_delete(self)).pack(side="right")

    def _pick_color(self):
        result = colorchooser.askcolor(color=self.color_var.get(),
                                       title="Pick region color")
        if result[1]:
            self.color_var.set(result[1])
            self.color_btn.color = result[1]

    def to_dict(self):
        return {
            "name": self.name_var.get(),
            "color": self.color_var.get(),
            "alpha": round(self.alpha_var.get(), 2),
        }

    def destroy(self):
        self.frame.destroy()


class ElectrodeRow:
    def __init__(self, parent, data, on_delete):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", padx=2, pady=2)

        ttk.Label(self.frame, text="Name").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=data.get("name", ""))
        ttk.Entry(self.frame, textvariable=self.name_var, width=10).grid(row=0, column=1, padx=(0, 6))

        ttk.Label(self.frame, text="Tip [x,y,z]").grid(row=0, column=2, sticky="w")
        tip = data.get("tip", [0, 0, 0])
        self.tip_x = tk.DoubleVar(value=tip[0])
        self.tip_y = tk.DoubleVar(value=tip[1])
        self.tip_z = tk.DoubleVar(value=tip[2])
        ttk.Entry(self.frame, textvariable=self.tip_x, width=7).grid(row=0, column=3)
        ttk.Entry(self.frame, textvariable=self.tip_y, width=7).grid(row=0, column=4)
        ttk.Entry(self.frame, textvariable=self.tip_z, width=7).grid(row=0, column=5, padx=(0, 6))

        ttk.Label(self.frame, text="Dir [dx,dy,dz]").grid(row=0, column=6, sticky="w")
        direction = data.get("direction", [0, 1, 0])
        self.dir_x = tk.DoubleVar(value=direction[0])
        self.dir_y = tk.DoubleVar(value=direction[1])
        self.dir_z = tk.DoubleVar(value=direction[2])
        ttk.Entry(self.frame, textvariable=self.dir_x, width=7).grid(row=0, column=7)
        ttk.Entry(self.frame, textvariable=self.dir_y, width=7).grid(row=0, column=8)
        ttk.Entry(self.frame, textvariable=self.dir_z, width=7).grid(row=0, column=9, padx=(0, 6))

        ttk.Label(self.frame, text="Depth").grid(row=0, column=10, sticky="w")
        self.depth_var = tk.DoubleVar(value=data.get("depth", 1000))
        ttk.Entry(self.frame, textvariable=self.depth_var, width=8).grid(row=0, column=11, padx=(0, 6))

        ttk.Label(self.frame, text="W").grid(row=0, column=12, sticky="w")
        self.lw_var = tk.IntVar(value=data.get("linewidth", 10))
        ttk.Spinbox(self.frame, from_=1, to=50, textvariable=self.lw_var,
                     width=4).grid(row=0, column=13, padx=(0, 6))

        self.color_var = tk.StringVar(value=data.get("color", "black"))
        self.color_btn = ColorButton(self.frame, color=self.color_var.get(),
                                     command=self._pick_color)
        self.color_btn.grid(row=0, column=14, padx=(0, 4))

        ttk.Button(self.frame, text="\u2715", width=3,
                   command=lambda: on_delete(self)).grid(row=0, column=15)

    def _pick_color(self):
        result = colorchooser.askcolor(color=self.color_var.get(),
                                       title="Pick electrode color")
        if result[1]:
            self.color_var.set(result[1])
            self.color_btn.color = result[1]

    def to_dict(self):
        return {
            "name": self.name_var.get(),
            "tip": [self.tip_x.get(), self.tip_y.get(), self.tip_z.get()],
            "direction": [self.dir_x.get(), self.dir_y.get(), self.dir_z.get()],
            "depth": self.depth_var.get(),
            "color": self.color_var.get(),
            "linewidth": self.lw_var.get(),
        }

    def destroy(self):
        self.frame.destroy()


class NavigatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Electrode Implant Navigator")
        self.root.minsize(900, 700)

        self.region_rows = []
        self.electrode_rows = []

        self._build_ui()
        self._load_defaults()

    def _build_ui(self):
        # --- Top settings bar ---
        top = ttk.LabelFrame(self.root, text="Settings", padding=6)
        top.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Label(top, text="Atlas:").grid(row=0, column=0, sticky="w")
        self.atlas_var = tk.StringVar(value=ATLASES[0])
        ttk.Combobox(top, textvariable=self.atlas_var, values=ATLASES,
                      width=22, state="readonly").grid(row=0, column=1, padx=(0, 12))

        ttk.Label(top, text="Shader:").grid(row=0, column=2, sticky="w")
        self.shader_var = tk.StringVar(value="plastic")
        ttk.Combobox(top, textvariable=self.shader_var, values=SHADER_STYLES,
                      width=10, state="readonly").grid(row=0, column=3, padx=(0, 12))

        self.axes_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Show Axes", variable=self.axes_var).grid(row=0, column=4, padx=(0, 12))

        ttk.Label(top, text="Zoom:").grid(row=0, column=5, sticky="w")
        self.zoom_var = tk.DoubleVar(value=1.4)
        ttk.Spinbox(top, from_=0.5, to=5.0, increment=0.1,
                     textvariable=self.zoom_var, width=5).grid(row=0, column=6)

        # --- Auto-placement controls (row 1) ---
        sep = ttk.Separator(top, orient="horizontal")
        sep.grid(row=1, column=0, columnspan=8, sticky="ew", pady=3)
        ttk.Label(top, text="Auto N:").grid(row=2, column=0, sticky="w")
        self.auto_n_var = tk.IntVar(value=32)
        ttk.Spinbox(top, from_=1, to=128, textvariable=self.auto_n_var,
                     width=5).grid(row=2, column=1, padx=(0, 8))
        ttk.Button(top, text="Auto Place Electrodes",
                   command=self._auto_place).grid(row=2, column=2, columnspan=6, sticky="w")

        # --- Brain regions ---
        reg_frame = ttk.LabelFrame(self.root, text="Brain Regions", padding=6)
        reg_frame.pack(fill="x", padx=8, pady=4)

        reg_header = ttk.Frame(reg_frame)
        reg_header.pack(fill="x")
        for text, width in [("Region Name", 14), ("Color", 8), ("Alpha", 7)]:
            ttk.Label(reg_header, text=text, font=("", 9, "bold")).pack(side="left", padx=(0, 10) if text != "Alpha" else (0, 0))
        ttk.Button(reg_header, text="+ Add Region", command=self._add_region).pack(side="right")

        self.regions_scroll = ScrollableFrame(reg_frame)
        self.regions_scroll.pack(fill="x", pady=(4, 0))

        # --- Electrodes ---
        elec_frame = ttk.LabelFrame(self.root, text="Electrodes", padding=6)
        elec_frame.pack(fill="both", expand=True, padx=8, pady=4)

        elec_header = ttk.Frame(elec_frame)
        elec_header.pack(fill="x")
        ttk.Label(elec_header, text="Tip = deep insertion point. Direction = unit vector toward skull surface.",
                  foreground="gray").pack(side="left")
        ttk.Button(elec_header, text="+ Add Electrode", command=self._add_electrode).pack(side="right")

        self.electrodes_scroll = ScrollableFrame(elec_frame)
        self.electrodes_scroll.pack(fill="both", expand=True, pady=(4, 0))

        # --- Bottom buttons ---
        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill="x")

        ttk.Button(bottom, text="Save Config", command=self._save_config).pack(side="left", padx=(0, 6))
        ttk.Button(bottom, text="Load Config", command=self._load_config).pack(side="left", padx=(0, 6))
        ttk.Button(bottom, text="Generate 3D View", command=self._generate).pack(side="right")

    def _load_defaults(self):
        for r in DEFAULT_REGIONS:
            self._add_region(r)
        for e in DEFAULT_ELECTRODES:
            self._add_electrode(e)

    # --- Auto Placement ---

    def _auto_place(self):
        """Auto-generate electrodes distributed across all brain regions."""
        regions = [r.to_dict() for r in self.region_rows if r.name_var.get().strip()]
        if not regions:
            messagebox.showwarning("No Regions",
                                   "Add at least one brain region first.")
            return

        n_total = self.auto_n_var.get()
        if n_total < 1:
            return

        import numpy as np
        try:
            from brainrender import Scene
        except ImportError:
            messagebox.showerror("Error",
                                 "brainrender is not installed.\n"
                                 "Run: pip install brainrender")
            return

        atlas_name = self.atlas_var.get()

        # Clear existing electrodes
        for row in self.electrode_rows:
            row.destroy()
        self.electrode_rows.clear()

        # Show a "loading" cursor while atlas loads
        self.root.config(cursor="watch")
        self.root.update()
        try:
            scene = Scene(atlas_name=atlas_name, inset=False)
        except Exception as exc:
            self.root.config(cursor="")
            messagebox.showerror("Atlas Error",
                                 f"Could not load atlas \"{atlas_name}\":\n{exc}")
            return

        region_names = [r["name"] for r in regions]
        n_regions = len(region_names)

        # Evenly distribute electrodes
        counts = [n_total // n_regions] * n_regions
        for i in range(n_total % n_regions):
            counts[i] += 1

        np.random.seed(42)
        dv_entry = 400.0

        for r_name, n in zip(region_names, counts):
            actor = scene.add_brain_region(r_name, alpha=0.3)
            verts = actor.mesh.points
            centroid = verts.mean(axis=0)

            if n <= len(verts):
                indices = np.random.choice(len(verts), n, replace=False)
                targets = verts[indices]
            else:
                targets = verts[np.random.choice(len(verts), n, replace=True)]

            # Bias toward centroid for tighter clustering
            targets = 0.7 * targets + 0.3 * centroid

            for tgt in targets:
                entry = [float(tgt[0]), dv_entry, float(tgt[2])]
                vec = tgt - np.array(entry)
                dist = float(np.linalg.norm(vec))
                direction = (vec / dist).tolist() if dist > 0 else [0, 1, 0]

                data = {
                    "name": "",
                    "tip": [round(entry[0], 1), round(entry[1], 1), round(entry[2], 1)],
                    "direction": [round(direction[0], 4), round(direction[1], 4), round(direction[2], 4)],
                    "depth": round(dist, 2),
                    "color": "black",
                    "linewidth": 4,
                }
                self._add_electrode(data)

        self.root.config(cursor="")
        messagebox.showinfo("Auto Placement",
                            f"Generated {n_total} electrodes across "
                            f"{n_regions} region(s).")

    # --- Region management ---

    def _add_region(self, data=None):
        if data is None:
            data = {"name": "", "color": "gray", "alpha": 0.5}
        row = RegionRow(self.regions_scroll.inner, data, self._remove_region)
        self.region_rows.append(row)

    def _remove_region(self, row):
        row.destroy()
        self.region_rows.remove(row)

    # --- Electrode management ---

    def _add_electrode(self, data=None):
        if data is None:
            data = {"name": "", "tip": [0, 0, 0], "direction": [0, 1, 0],
                    "depth": 1000, "color": "black", "linewidth": 10}
        row = ElectrodeRow(self.electrodes_scroll.inner, data, self._remove_electrode)
        self.electrode_rows.append(row)

    def _remove_electrode(self, row):
        row.destroy()
        self.electrode_rows.remove(row)

    # --- Config I/O ---

    def _build_config(self):
        return {
            "atlas_name": self.atlas_var.get(),
            "render_settings": {
                "show_axes": self.axes_var.get(),
                "whole_screen": False,
                "shader_style": self.shader_var.get(),
                "zoom": round(self.zoom_var.get(), 1),
            },
            "brain_regions": [r.to_dict() for r in self.region_rows if r.name_var.get().strip()],
            "electrodes": [e.to_dict() for e in self.electrode_rows if e.name_var.get().strip()],
        }

    def _save_config(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="config.json",
        )
        if path:
            with open(path, "w") as f:
                json.dump(self._build_config(), f, indent=4)
            messagebox.showinfo("Saved", f"Config saved to {path}")

    def _load_config(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path) as f:
            config = json.load(f)

        self.atlas_var.set(config.get("atlas_name", ATLASES[0]))
        rs = config.get("render_settings", {})
        self.shader_var.set(rs.get("shader_style", "plastic"))
        self.axes_var.set(rs.get("show_axes", False))
        self.zoom_var.set(rs.get("zoom", 1.4))

        for row in self.region_rows:
            row.destroy()
        self.region_rows.clear()
        for r in config.get("brain_regions", []):
            self._add_region(r)

        for row in self.electrode_rows:
            row.destroy()
        self.electrode_rows.clear()
        for e in config.get("electrodes", []):
            self._add_electrode(e)

    # --- Generate ---

    def _generate(self):
        config = self._build_config()

        if not config["brain_regions"] and not config["electrodes"]:
            messagebox.showwarning("Nothing to render",
                                   "Add at least one brain region or electrode.")
            return

        tmp_path = str(Path(__file__).parent / "_gui_config.json")
        with open(tmp_path, "w") as f:
            json.dump(config, f, indent=4)

        script = str(Path(__file__).parent / "implant_navigator.py")
        proc = subprocess.Popen([sys.executable, script, "--config", tmp_path])

        messagebox.showinfo("Rendering",
                            "brainrender window opened.\n"
                            "Close it when done, or click OK to continue.")


def main():
    root = tk.Tk()
    NavigatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
