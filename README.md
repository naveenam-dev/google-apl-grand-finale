# Aegis Arena: Decentralized Stadium Agent Mesh

Aegis Arena is an advanced, real-time command-and-control platform designed to manage stadium crowd safety, bottlenecks, and incidents. It is structured using a state-of-the-art **React Frontend** and a high-performance **Python (FastAPI) Backend**, utilizing a **Decentralized Multi-Agent Mesh** communicating asynchronously via WebSockets and an Event Bus.

---

## Technical Architecture

<img width="900" height="423" alt="image" src="https://github.com/user-attachments/assets/e0b3d410-700a-4c90-aced-ef716c0f1816" />



The platform is divided into two decoupled layers:

```text
APLGrandFinale/Code/
├── backend/
│   ├── main.py               # FastAPI server, WebSocket hub, Python Agent Mesh
│   └── requirements.txt      # Python dependencies (fastapi, uvicorn, websockets)
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React Dashboard Component
│   │   ├── index.css         # Translucent CSS styling, animations, and flows
│   │   └── main.jsx          # React mounting entrypoint
│   ├── index.html            # Vite HTML mount container
│   ├── package.json          # Node dependencies (lucide-react, etc.)
│   └── vite.config.js        # Vite configurations
└── README.md                 # Project architecture documentation
```

### 1. Python Backend (`/backend`)
- **FastAPI / Uvicorn**: High-speed ASGI server driving HTTP REST APIs and WebSockets.
- **Asynchronous Agent Mesh**: The specialized autonomous agents run natively in Python:
  - **`GateAgent`**: Monitors turns rate and predicts surges.
  - **`RoutingAgent`**: Calculates bottlenecks, alters signage, and dispatches app alerts.
  - **`SafetyAgent`**: Overrides system parameters and handles emergency dispatches.
- **Real-Time Websocket (`/ws`)**: Streams instant JSON telemetry updates, agent visual nodes, event streams, and alerts directly to React.

### 2. React Frontend (`/frontend`)
- **Vite React**: A fast, hot-reloading user interface.
- **Unified HUD Metrics**: Automatically synchronizes state from the WebSocket pipeline.
- **Interactive SVG Blueprint**: Renders stands heatmaps, color-coded gates, flow directions, and animating responder tokens translating smoothly across coordinates.
- **Agent Console UI**: Real-time thinking badge nodes and glowing tool indicator badges showing what toolkit APIs agents are invoking in Python.
- **Smartphone Alert**: Slide-in smart push alert mockups displaying custom directional notices.

---

## Installation & Running Locally

Ensure you have **Node.js** and **Python 3.10+** installed on your system.

### 🐍 1. Start Python Backend
Open a terminal in the project root and navigate to the `backend` folder:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --port 8000 --host 127.0.0.1
```
The backend API is now online at `http://127.0.0.1:8000` and WebSocket listener at `ws://127.0.0.1:8000/ws`.

### ⚛️ 2. Start React Frontend
Open another terminal, navigate to the `frontend` folder:
```bash
cd frontend
npm install
npm run dev -- --port 8080 --host 127.0.0.1
```
The React frontend dashboard is now online at **[http://127.0.0.1:8080](http://127.0.0.1:8080)**.

---
## UI
<img width="1860" height="878" alt="image" src="https://github.com/user-attachments/assets/9c7b8161-f7b5-4959-b41f-d3627adc9e3c" />

## Simulator Walkthrough Steps

1. **Access the Console**: Navigate to `http://127.0.0.1:8080` in your web browser.
2. **Interactive blueprints**: Click Stand sectors or Gate turnstiles on the map. Verify React opens live telemetry overlays fetched via WebSocket.
3. **Trigger Exit Surge**: Click **Post-Match Exit Surge** under Incident Simulator. Watch the python **GateAgent** invoke its surge predictions, publish `GATE_CONGESTION` to the event bus, which the **RoutingAgent** intercepts, pushing a mock smartphone warning toast onto the screen!
4. **Trigger Security Incident**: Blocks Gate 5, flashes the crimson emergency overlay, and automatically dispatches responder squads sliding smoothly towards coordinates with live ETA tick updates.

## Scalability
<img width="900" height="588" alt="image" src="https://github.com/user-attachments/assets/b1468b01-4db6-4c9d-a6f5-814c8a09ca53" />


