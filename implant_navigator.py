import json
import argparse
from pathlib import Path

import numpy as np
from brainrender import Scene, settings
from brainrender.actors import Line


def load_config(path):
    with open(path) as f:
        return json.load(f)


def compute_endpoint(tip, direction, depth):
    tip = np.array(tip, dtype=float)
    direction = np.array(direction, dtype=float)
    direction = direction / np.linalg.norm(direction)
    return tip + direction * depth


def apply_render_settings(render_settings):
    for key, value in render_settings.items():
        attr = key.upper()
        if hasattr(settings, attr):
            setattr(settings, attr, value)


def main():
    parser = argparse.ArgumentParser(
        description="3D brain volume with highlighted regions and electrode positions"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON config file (default: config.json next to this script)",
    )
    args = parser.parse_args()

    if args.config is None:
        args.config = str(Path(__file__).parent / "config.json")

    config = load_config(args.config)

    apply_render_settings(config.get("render_settings", {}))

    scene = Scene(
        atlas_name=config.get("atlas_name"),
        inset=False,
    )

    for region in config.get("brain_regions", []):
        scene.add_brain_region(
            region["name"],
            alpha=region.get("alpha", 0.5),
            color=region.get("color"),
        )

    for electrode in config.get("electrodes", []):
        tip = electrode["tip"]
        direction = electrode["direction"]
        depth = electrode["depth"]
        top = compute_endpoint(tip, direction, depth)

        shank = Line(
            coordinates=[tip, top.tolist()],
            linewidth=electrode.get("linewidth", 10),
            color=electrode.get("color", "black"),
            name=electrode.get("name"),
        )
        scene.add(shank)

    scene.render(zoom=config.get("render_settings", {}).get("zoom", 1.4))


if __name__ == "__main__":
    main()
