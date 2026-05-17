import json
import numpy as np
from vedo import Mesh, Points, Lines, show
import os

def visualize_results(mesh_path, topo_path):
    actors = []

    print("Loading mesh...")
    try:
        mesh = Mesh(mesh_path).color("lightgray")
        actors.append(mesh)
    except Exception as e:
        print(f"Error loading mesh: {e}")

    print("Loading topology...")
    try:
        with open(topo_path, "r") as f:
            topo = json.load(f)

        if 'corners' in topo and len(topo['corners']) > 0:
            corners = np.array(topo['corners'])
            pts = Points(corners, r=12).color("red")
            actors.append(pts)
            print(f"Добавлено {len(corners)} углов.")

        if 'curves' in topo:
            for curve in topo['curves']:
                if 'pv_points' in curve and 'pv_lines' in curve:
                    points = np.array(curve['pv_points'])
                    lines_idx = np.array(curve['pv_lines'])
                    
                    starts = points[lines_idx[:, 0]]
                    ends = points[lines_idx[:, 1]]
                    
                    lines_actor = Lines(starts, ends).color("blue").linewidth(4)
                    actors.append(lines_actor)
                    
            print(f"Added {len(topo['curves'])} curves")
    except Exception as e:
        print(f"Error loading topology: {e}")

    print("Launching visualization...")
    show(actors, axes=1, bg="white", title="visualize")

if __name__ == "__main__":
    base = "/home/daniil/scan2cad/point2cad"
    mesh_f = os.path.join(base, "out/clipped/mesh.ply")
    topo_f = os.path.join(base, "out/topo/topo.json")
    
    visualize_results(mesh_f, topo_f)
