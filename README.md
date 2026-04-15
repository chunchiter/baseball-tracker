# Baseball Tracker

Sistema de tracking de trayectoria de pelota de béisbol en tiempo real usando visión computacional e inteligencia artificial.

## Demo
- Detección de pelota en tiempo real con YOLOv8
- Trayectoria dibujada frame a frame
- Cálculo de velocidad en km/h
- Guardado automático de sesiones y lanzamientos
- Dashboard web en tiempo real con cámara en vivo

## Stack tecnológico
- **Python 3.11**
- **YOLOv8** — detección de objetos
- **OpenCV** — captura y procesamiento de video
- **PyTorch + CUDA** — inferencia en GPU (RTX 4050)
- **FastAPI + WebSocket** — backend API en tiempo real
- **React + Vite + Recharts** — dashboard web
- **Three.js** — visualización 3D (próximamente)

## Requisitos de hardware
- GPU NVIDIA (probado en RTX 4050 Laptop GPU)
- Cámara mínimo 30fps
- RAM 16GB recomendado

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/baseball-tracker.git
cd baseball-tracker
```

### 2. Crear entorno virtual
```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

### 3. Instalar PyTorch con CUDA
Visita https://pytorch.org, selecciona tu versión de CUDA y copia el comando de instalación.

### 4. Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### 5. Instalar dependencias del dashboard
```bash
cd dashboard
npm install
cd ..
```

### 6. Descargar dataset y entrenar el modelo
```bash
python train.py
```

## Cómo correr el proyecto

### Solo el detector (modo local)
```bash
python test_detector.py
```

### Backend + Dashboard (modo completo)
Abrir dos terminales:

**Terminal 1 — Backend:**
```bash
venv\Scripts\activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Dashboard:**
```bash
cd dashboard
npm run dev
```

Luego abrir en el navegador: **http://localhost:5173**

## Controles (modo local)
| Tecla | Acción |
|---|---|
| Q | Salir y guardar sesión |
| G | Ver gráfica del último lanzamiento |

## Estructura del proyecto

baseball-tracker/
├── backend/
│   ├── main.py          # API FastAPI + WebSocket
│   └── tracker.py       # Lógica del detector
├── dashboard/
│   └── src/
│       ├── App.jsx      # Dashboard principal
│       └── App.css      # Estilos
├── dataset/             # Dataset de entrenamiento (no incluido)
├── runs/                # Resultados del entrenamiento (no incluido)
├── trajectories/        # Sesiones guardadas en JSON
├── train.py             # Script de entrenamiento
├── test_detector.py     # Detector con ventana local
├── show_trajectory.py   # Visualizador de trayectorias
└── requirements.txt


## Roadmap
- [x] Detección de pelota con YOLOv8
- [x] Tracking de trayectoria en tiempo real
- [x] Cálculo de velocidad en km/h
- [x] Guardado de sesiones en JSON
- [x] Backend API con FastAPI + WebSocket
- [x] Dashboard web con React + cámara en vivo
- [x] Trayectoria visual en el dashboard
- [x] Historial de lanzamientos en el dashboard
- [x] Zona de strike interactiva
- [ ] Calibración automática de cámara
- [ ] Overlay para OBS

## Modelo entrenado
- Dataset: 7,031 imágenes de béisbol
- Épocas: 50
- mAP50: 91.9%
- Precisión: 92.7%
- Recall: 84.6%
