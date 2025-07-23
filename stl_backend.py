
import io
import numpy as np
from typing import Tuple
from vedo import load as vedo_load, Mesh, Text2D, Plotter
import tempfile, os
import imageio.v3 as iio

def load_stl_bytes(file_bytes: bytes, file_name: str = "uploaded.stl") -> Mesh:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        tmp_path = tmp.name
    mesh = vedo_load(tmp_path)
    try:
        os.remove(tmp_path)
    except OSError:
        pass
    return mesh

def clone_mesh(mesh: Mesh) -> Mesh:
    return mesh.clone() if mesh is not None else None

def apply_transform(mesh: Mesh, axis: str, angle_deg: float, dx: float, dy: float, dz: float) -> Mesh:
    newm = mesh.clone()
    axis = axis.upper()
    if axis == "X":
        newm.rotate(angle_deg, axis=(1, 0, 0))
    elif axis == "Y":
        newm.rotate(angle_deg, axis=(0, 1, 0))
    else:
        newm.rotate(angle_deg, axis=(0, 0, 1))
    newm.shift(dx, dy, dz)
    return newm

def mesh_bounds_text(mesh: Mesh) -> str:
    b = mesh.bounds()
    xmin, xmax, ymin, ymax, zmin, zmax = b
    return (f"X: {xmin:.2f} ~ {xmax:.2f}\n"
            f"Y: {ymin:.2f} ~ {ymax:.2f}\n"
            f"Z: {zmin:.2f} ~ {zmax:.2f}")

def render_snapshot(mesh: Mesh, size: Tuple[int, int] = (600, 600)) -> bytes:
    btxt = mesh_bounds_text(mesh)
    text = Text2D(btxt, pos='top-left', s=0.9, c='k')
    vp = Plotter(offscreen=True, size=size, title="STL Preview", axes=0)
    vp.show(mesh, text, viewup="z", resetcam=True)
    arr = vp.screenshot(returnNumpy=True)
    vp.close()
    png_bytes = iio.imwrite(".png", arr, extension=".png")
    return png_bytes

def mesh_to_stl_bytes(mesh: Mesh) -> bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        tmp_path = tmp.name
    mesh.write(tmp_path)
    with open(tmp_path, "rb") as f:
        data = f.read()
    try:
        os.remove(tmp_path)
    except OSError:
        pass
    return data
