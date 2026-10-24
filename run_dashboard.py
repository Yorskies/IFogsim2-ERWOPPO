"""
run_dashboard.py
----------------
Skrip peluncur cepat untuk ERWO-PPO Live Web Dashboard.
Menjalankan server FastAPI di http://127.0.0.1:8000.
"""

import sys
import os
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jalankan ERWO-PPO Web Dashboard Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Auto reload server")
    args = parser.parse_args()

    print("=" * 75)
    print("        [+] ERWO-PPO LIVE WEB DASHBOARD SERVER BERJALAN [+]        ")
    print("=" * 75)
    print(f"  * URL Dashboard  : http://{args.host}:{args.port}")
    print(f"  * WebSocket Stream: ws://{args.host}:{args.port}/ws")
    print("  * Buka tautan di atas pada browser untuk melihat visualisasi live.")
    print("  * Tekan CTRL+C untuk menghentikan server.")
    print("=" * 75)

    uvicorn.run("dashboard.server:app", host=args.host, port=args.port, reload=args.reload)
