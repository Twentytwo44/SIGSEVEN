# app/api/ws_manager.py
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # 🔥 บรรทัดนี้สำคัญที่สุด! ต้องมีคำสั่งสับสวิตช์รับสายตรงนี้ครับ
        await websocket.accept() 
        self.active_connections.append(websocket)
        print("✅ [WS Manager] ปลดล็อกรับการเชื่อมต่อสำเร็จ")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("Client disconnected.")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except RuntimeError:
                pass 

manager = ConnectionManager()