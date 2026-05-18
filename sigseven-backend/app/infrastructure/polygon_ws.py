import asyncio
import websockets
import json
import pandas as pd
import time
import os
from dotenv import load_dotenv
from app.core.engine import SMA4Analyzer
from app.api.ws_manager import manager

# โหลด API Key ของ Alpaca
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

analyzer = SMA4Analyzer()

async def live_market_data_stream():
    # URL ของ Alpaca สำหรับข้อมูลหุ้นอเมริกาฟรี (IEX Network)
    uri = "wss://stream.data.alpaca.markets/v2/iex"
    df = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close'])

    while True:
        try:
            print("🔌 กำลังเชื่อมต่อไปที่ Alpaca (Free Real-time US Stocks)...")
            async with websockets.connect(uri) as ws:
                
                # 1. ยืนยันตัวตนด้วย API Key และ Secret
                auth_message = {
                    "action": "auth",
                    "key": API_KEY,
                    "secret": SECRET_KEY
                }
                await ws.send(json.dumps(auth_message))
                auth_response = await ws.recv()
                print(f"🔑 สถานะยืนยันตัวตน: {auth_response}")

                # 2. ขอรับข้อมูลกราฟ 1 นาที (bars) ของหุ้น SPY
                sub_message = {
                    "action": "subscribe",
                    "bars": ["SPY"]
                }
                await ws.send(json.dumps(sub_message))
                sub_response = await ws.recv()
                print(f"📡 สถานะการดึงข้อมูล: {sub_response}")
                print("⚡ ระบบพร้อมรับข้อมูล Real-time ฟรี 100% (รอตลาดเปิด)...")
                print("-" * 50)

                while True:
                    message = await ws.recv()
                    data = json.loads(message)

                    for event in data:
                        # Alpaca ใช้ตัว 'b' เป็นสัญลักษณ์ของข้อมูล Bar (แท่งเทียน)
                        if event.get('T') == 'b':
                            new_candle = {
                                'Open': float(event.get('o', 0)),
                                'High': float(event.get('h', 0)),
                                'Low': float(event.get('l', 0)),
                                'Close': float(event.get('c', 0))
                            }
                            
                            print(f"📊 [LIVE ALPACA] SPY แท่งใหม่ปิดที่ -> ${new_candle['Close']}")

                            df.loc[len(df)] = new_candle
                            df = df.tail(20).reset_index(drop=True)

                            signal = analyzer.analyze_candle(df, ticker="SPY")

                            if signal:
                                payload = {
                                    "id": int(time.time()),
                                    "timestamp": time.strftime("%H:%M:%S"),
                                    **signal
                                }
                                print(f"🚨 SIGNAL FIRED: {payload['option_type']} {payload['underlying']} Strike ${payload['strike']}")
                                await manager.broadcast(payload)
                                        
        except Exception as e:
            print(f"⚠️ เซิร์ฟเวอร์ตัดการเชื่อมต่อ (ตลาดปิดทำการ): {e}")
            print("⏳ จะลองเชื่อมต่อใหม่ใน 10 วินาที...")
            await asyncio.sleep(10)