# Electrode Implant Navigator

3D brain volume viewer for planning electrode implant positions in mouse and rat brains, built on [brainrender](https://docs.brainrender.info/).

## Features

- Visualize specific brain regions with custom colors and transparency
- Position electrode shanks using tip coordinates, direction vectors, and depth
- Support for mouse (Allen) and rat (Waxholm Space) atlases
- GUI for interactive configuration — no code editing needed
- Save/load experiment configurations as JSON files

## Installation

Requires Python 3.9+ and a conda environment (recommended).

```bash
conda create -n electrode_implant python=3.12
conda activate electrode_implant
pip install -r requirements.txt
```

The first run will download the selected atlas (~500 MB for mouse, ~200 MB for rat).

## Usage

### GUI (recommended)

```bash
python gui.py
```

The GUI lets you:
- Select atlas (mouse/rat) and render settings
- Add/remove brain regions with name, color, and transparency
- Add/remove electrodes with tip coordinates, direction, depth, color, and width
- Save/load configurations as JSON
- Launch the 3D viewer with one click

### Command line

```bash
python implant_navigator.py                          # uses config.json
python implant_navigator.py --config my_config.json  # uses custom config
```

## Configuration

Configs are JSON files with this structure:

```json
{
    "atlas_name": "allen_mouse_25um",
    "render_settings": {
        "show_axes": false,
        "whole_screen": false,
        "shader_style": "plastic",
        "zoom": 1.4
    },
    "brain_regions": [
        {"name": "ILA", "color": "darkgreen", "alpha": 0.5}
    ],
    "electrodes": [
        {
            "name": "shank1",
            "tip": [7200, 1200, 8100],
            "direction": [0.0153, 0.9999, 0.0],
            "depth": 4900.57,
            "color": "black",
            "linewidth": 10
        }
    ]
}
```

### Electrode format

Each electrode is defined by:
- **tip**: `[x, y, z]` — insertion point (deep end, in atlas units)
- **direction**: `[dx, dy, dz]` — unit vector from tip toward skull surface (auto-normalized)
- **depth**: length of the shank in atlas units

### Available atlases

| Atlas name | Species | Resolution |
|---|---|---|
| `allen_mouse_25um` | Mouse | 25 µm |
| `allen_mouse_10um` | Mouse | 10 µm |
| `whs_sd_rat_39um` | Rat (Sprague-Dawley) | 39 µm |
| `swc_female_rat_50um` | Rat (female Wistar) | 50 µm |

## Project structure

```
├── gui.py                  # tkinter GUI for configuration
├── implant_navigator.py    # brainrender rendering script
├── config.json             # default experiment configuration
├── requirements.txt        # Python dependencies
└── README.md
```
