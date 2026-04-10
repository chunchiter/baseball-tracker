import json
import matplotlib.pyplot as plt
import sys
import os

def show_graph(filepath):
    with open(filepath, "r") as f:
        points = json.load(f)

    if len(points) < 2:
        print("Muy pocos puntos para graficar")
        return

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ys = [max(ys) - y + min(ys) for y in ys]

    plt.figure(figsize=(10, 5))
    plt.plot(xs, ys, 'r-o', markersize=4, linewidth=2)
    plt.scatter(xs[0], ys[0], color='green', s=150, zorder=5, label='Inicio')
    plt.scatter(xs[-1], ys[-1], color='blue', s=150, zorder=5, label='Final')
    plt.title(f"Trayectoria: {os.path.basename(filepath)}")
    plt.xlabel("Posición X (píxeles)")
    plt.ylabel("Posición Y (píxeles)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Toma el archivo más reciente si no se especifica uno
if len(sys.argv) > 1:
    filepath = sys.argv[1]
else:
    files = sorted(os.listdir("trajectories"))
    if not files:
        print("No hay trayectorias guardadas")
        exit()
    filepath = f"trajectories/{files[-1]}"
    print(f"Mostrando: {filepath}")

show_graph(filepath)