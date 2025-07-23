import numpy as np
from stl import mesh
import io
import tempfile
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt

def load_stl(file_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        path = tmp.name
    return mesh.Mesh.from_file(path)

def apply_transform(stl_mesh, axis, angle_deg, dx, dy, dz):
    angle_rad = np.deg2rad(angle_deg)
    rot_matrix = np.identity(3)
    if axis == "X":
        rot_matrix = np.array([[1, 0, 0],
                               [0, np.cos(angle_rad), -np.sin(angle_rad)],
                               [0, np.sin(angle_rad), np.cos(angle_rad)]])
    elif axis == "Y":
        rot_matrix = np.array([[np.cos(angle_rad), 0, np.sin(angle_rad)],
                               [0, 1, 0],
                               [-np.sin(angle_rad), 0, np.cos(angle_rad)]])
    elif axis == "Z":
        rot_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad), 0],
                               [np.sin(angle_rad), np.cos(angle_rad), 0],
                               [0, 0, 1]])

    stl_mesh.vectors = np.dot(stl_mesh.vectors, rot_matrix.T)
    stl_mesh.x += dx
    stl_mesh.y += dy
    stl_mesh.z += dz
    return stl_mesh

def render_mesh(stl_mesh):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.add_collection3d(mplot3d.art3d.Poly3DCollection(stl_mesh.vectors, alpha=0.3, edgecolor='k'))
    scale = stl_mesh.points.flatten()
    ax.auto_scale_xyz(scale, scale, scale)
    ax.set_box_aspect([1,1,1])
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf

def save_stl_bytes(stl_mesh):
    f = io.BytesIO()
    stl_mesh.save(f, mode=stl_mesh.mode)
    f.seek(0)
    return f
