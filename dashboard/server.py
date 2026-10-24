"""
server.py
---------
FastAPI WebSocket & REST Server untuk Real-time Live Dashboard ERWO-PPO.
Mendukung:
1. Penerimaan data telemetri eksternal (POST /api/push).
2. Broadcast WebSocket real-time (/ws) ke browser.
3. Kontrol simulasi interaktif dari browser (Play, Pause, Reset, Ganti Metode, Slider Delay).
4. Worker simulasi internal mandiri (dapat dijalankan langsung dari browser).
"""

import os
import sys
import json
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
import uvicorn
import numpy as np

# Pastikan root workspace ada di sys.path agar dapat mengimpor modul proyek
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

app = FastAPI(title="ERWO-PPO Real-time Research Dashboard", version="1.0.0")

# Mount folder static
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


# ==============================================================================
# WEBSOCKET MANAGER
# ==============================================================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


# ==============================================================================
# DATA MODELS
# ==============================================================================
class SimulationData(BaseModel):
    step: int
    action: int
    load_imbalance: float
    reward: float
    latency: float
    energy: float
    deadline: float
    node_cpu: List[float]  # 7 nodes
    # Enhanced attributes
    node_queues: Optional[List[float]] = None
    node_latencies: Optional[List[float]] = None
    is_violated: Optional[bool] = False
    qos_satisfaction: Optional[float] = 0.0
    task_data_size: Optional[float] = 0.0
    task_mi: Optional[float] = 0.0
    task_deadline: Optional[float] = 0.0
    task_priority: Optional[float] = 0.0
    method_name: Optional[str] = "ERWO-PPO"
    workload: Optional[str] = "dynamic"
    episode: Optional[int] = 1
    # 100 Edge Devices Fleet Telemetry
    source_device_id: Optional[int] = 0
    mean_fleet_battery: Optional[float] = 1.0
    depleted_devices_count: Optional[int] = 0
    devices_battery: Optional[List[float]] = None


class ControlCommand(BaseModel):
    command: str = Field(..., description="play, pause, reset, step, set_speed, set_method, set_workload")
    value: Optional[Any] = None


# ==============================================================================
# INTERNAL SIMULATION CONTROLLER & WORKER
# ==============================================================================
class SimState:
    is_running: bool = False
    is_paused: bool = False
    speed_ms: int = 150  # milliseconds per step
    current_method: str = "ERWO-PPO"
    current_workload: str = "dynamic"
    current_episode: int = 1
    current_step: int = 0
    env: Any = None
    model: Any = None
    obs: Any = None
    worker_task: Optional[asyncio.Task] = None


sim_state = SimState()


def get_policy_model(method_name: str):
    """Memuat model PPO terlatih atau instance heuristik."""
    try:
        from agent_baselines import (
            LocalOnlyPolicy,
            CloudOnlyPolicy,
            NearestFogPolicy,
            LeastLoadedFogPolicy,
        )
    except Exception as e:
        print(f"[SimWorker] Error import baselines: {e}")
        return None

    if method_name == "ERWO-PPO":
        model_path = os.path.join(ROOT_DIR, "models", "ppo_ifogsim2_erwo.zip")
        if os.path.exists(model_path):
            try:
                from stable_baselines3 import PPO
                print(f"[SimWorker] Memuat model PPO dari {model_path}")
                return PPO.load(model_path)
            except Exception as e:
                print(f"[SimWorker] Gagal memuat PPO: {e}, fallback ke LeastLoaded")
                return LeastLoadedFogPolicy()
        else:
            print("[SimWorker] Model PPO belum ditemukan, fallback ke LeastLoadedFogPolicy")
            return LeastLoadedFogPolicy()
    elif method_name == "Least-loaded fog":
        return LeastLoadedFogPolicy()
    elif method_name == "Nearest-fog":
        return NearestFogPolicy()
    elif method_name == "Cloud-only":
        return CloudOnlyPolicy()
    elif method_name == "Local-only":
        return LocalOnlyPolicy()
    else:
        # Default Random
        class RandomPolicy:
            def predict(self, obs, deterministic=True):
                return int(np.random.randint(0, 7)), None
        return RandomPolicy()


async def simulation_loop():
    """Loop background yang mengeksekusi simulasi step-by-step."""
    from env_ifogsim2 import iFogSim2Env

    print("[SimWorker] Memulai background simulation loop...")

    while True:
        try:
            if not sim_state.is_running or sim_state.is_paused:
                await asyncio.sleep(0.1)
                continue

            # Inisialisasi env jika belum ada
            if sim_state.env is None:
                sim_state.env = iFogSim2Env(workload=sim_state.current_workload)
                sim_state.env.disable_dashboard = True  # Worker sendiri yang mem-broadcast
                sim_state.obs, _ = sim_state.env.reset(seed=1000 + sim_state.current_episode)
                sim_state.current_step = 0
                sim_state.model = get_policy_model(sim_state.current_method)

            # Prediksi aksi
            if sim_state.model is not None:
                action, _ = sim_state.model.predict(sim_state.obs, deterministic=True)
                if isinstance(action, np.ndarray):
                    action = int(action.item())
                else:
                    action = int(action)
            else:
                action = int(np.random.randint(0, 7))

            # Step simulasi
            obs, total_reward, done, truncated, info = sim_state.env.step(action)
            sim_state.obs = obs
            sim_state.current_step = info.get("step", sim_state.current_step + 1)

            # Siapkan payload
            payload = SimulationData(
                step=sim_state.current_step,
                action=action,
                load_imbalance=float(info.get("load_imbalance", np.std(obs[0:7]))),
                reward=float(total_reward),
                latency=float(info.get("latency_score", 0.0)),
                energy=float(info.get("energy_efficiency", 0.0)),
                deadline=float(info.get("deadline_compliance", 0.0)),
                node_cpu=[float(x) for x in obs[0:7]],
                node_queues=[float(x) for x in obs[28:35]],
                node_latencies=[float(x) for x in obs[21:28]],
                is_violated=bool(info.get("is_violated", False)),
                qos_satisfaction=float(info.get("qos_satisfaction", 0.0)),
                task_data_size=float(obs[42]) if len(obs) > 42 else 0.0,
                task_mi=float(obs[43]) if len(obs) > 43 else 0.0,
                task_deadline=float(obs[44]) if len(obs) > 44 else 0.0,
                task_priority=float(obs[45]) if len(obs) > 45 else 0.0,
                method_name=sim_state.current_method,
                workload=sim_state.current_workload,
                episode=sim_state.current_episode,
                source_device_id=int(info.get("source_device_id", 0)),
                mean_fleet_battery=float(info.get("mean_fleet_battery", 1.0)),
                depleted_devices_count=int(info.get("depleted_devices_count", 0)),
                devices_battery=info.get("devices_battery", []),
            )

            await manager.broadcast(payload.model_dump_json())

            if done or truncated:
                sim_state.current_episode += 1
                sim_state.obs, _ = sim_state.env.reset(seed=1000 + sim_state.current_episode)
                sim_state.current_step = 0
                await asyncio.sleep(0.5)

            delay_sec = max(0.02, sim_state.speed_ms / 1000.0)
            await asyncio.sleep(delay_sec)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[SimWorker] Error dalam loop simulasi: {e}")
            await asyncio.sleep(1.0)


@app.on_event("startup")
async def startup_event():
    sim_state.worker_task = asyncio.create_task(simulation_loop())
    print("[Server] Background simulation worker aktif.")


@app.on_event("shutdown")
async def shutdown_event():
    if sim_state.worker_task:
        sim_state.worker_task.cancel()
    if sim_state.env:
        try:
            sim_state.env.close()
        except Exception:
            pass


# ==============================================================================
# ENDPOINTS
# ==============================================================================
@app.post("/api/push")
async def push_data(data: SimulationData):
    """Menerima telemetri dari proses luar (misal run_demo.py atau main.py)."""
    await manager.broadcast(data.model_dump_json())
    return {"status": "success"}


@app.get("/api/status")
async def get_status():
    """Mengembalikan status live server dan simulasi."""
    return {
        "is_running": sim_state.is_running,
        "is_paused": sim_state.is_paused,
        "speed_ms": sim_state.speed_ms,
        "current_method": sim_state.current_method,
        "current_workload": sim_state.current_workload,
        "current_episode": sim_state.current_episode,
        "current_step": sim_state.current_step,
        "active_clients": len(manager.active_connections),
    }


@app.post("/api/control")
async def control_simulation(ctrl: ControlCommand):
    """Mengendalikan simulasi dari antarmuka Web UI."""
    cmd = ctrl.command.lower()
    val = ctrl.value

    if cmd == "play":
        sim_state.is_running = True
        sim_state.is_paused = False
        if sim_state.env is None:
            sim_state.model = get_policy_model(sim_state.current_method)
    elif cmd == "pause":
        sim_state.is_paused = True
    elif cmd == "resume":
        sim_state.is_paused = False
        sim_state.is_running = True
    elif cmd == "reset":
        sim_state.is_running = False
        sim_state.is_paused = False
        if sim_state.env is not None:
            try:
                sim_state.env.close()
            except Exception:
                pass
            sim_state.env = None
        sim_state.current_step = 0
        sim_state.current_episode = 1
        # Broadcast status reset
        await manager.broadcast(json.dumps({"type": "reset"}))
    elif cmd == "set_speed":
        try:
            sim_state.speed_ms = max(20, int(val))
        except (ValueError, TypeError):
            pass
    elif cmd == "set_method":
        sim_state.current_method = str(val)
        sim_state.model = get_policy_model(sim_state.current_method)
    elif cmd == "set_workload":
        sim_state.current_workload = str(val)
        if sim_state.env is not None:
            sim_state.env.set_workload(sim_state.current_workload)
            sim_state.obs, _ = sim_state.env.reset(seed=1000 + sim_state.current_episode)

    return {"status": "ok", "command": cmd, "value": val}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Kirim status awal
    try:
        await websocket.send_text(
            json.dumps({
                "type": "init",
                "status": {
                    "is_running": sim_state.is_running,
                    "is_paused": sim_state.is_paused,
                    "speed_ms": sim_state.speed_ms,
                    "method": sim_state.current_method,
                    "workload": sim_state.current_workload,
                }
            })
        )
    except Exception:
        pass

    try:
        while True:
            # Terima pesan/perintah langsung dari websocket jika ada
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
                if "command" in msg:
                    await control_simulation(ControlCommand(command=msg["command"], value=msg.get("value")))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ERWO-PPO Real-time Web Dashboard Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    args = parser.parse_args()

    print("=" * 70)
    print("   ERWO-PPO LIVE WEB DASHBOARD SERVER   ")
    print(f"   Akses Dashboard di Browser: http://{args.host}:{args.port}")
    print("=" * 70)
    uvicorn.run("dashboard.server:app", host=args.host, port=args.port, reload=False)
