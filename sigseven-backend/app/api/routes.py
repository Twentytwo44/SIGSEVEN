# app/api/routes.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Query
from app.api.ws_manager import manager
from app.core.engine import SMA4Analyzer
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import asyncio
import time
import json
from datetime import datetime

router = APIRouter()
live_streaming_task = None

async def stream_live_market_data(pair_symbol: str):
    # แปลงชื่อคู่เงินให้มีขอบคั่นสำหรับแสดงผล เช่น "EURUSD" -> "EUR/USD"
    display_name = f"{pair_symbol[:3]}/{pair_symbol[3:]}" if len(pair_symbol) == 6 else pair_symbol
    
    print(f"📡 [LIVE] กำลังเชื่อมต่อท่อ TradingView Live Stream สำหรับคู่เงิน {display_name}...")
    try:
        tv = TvDatafeed()
    except Exception as e:
        print(f"❌ [LIVE] ไม่สามารถเริ่มไลบรารี TradingView ได้: {e}")
        return

    analyzer = SMA4Analyzer()
    now = datetime.now()
    elapsed_minutes = now.hour * 60 + now.minute
    init_bars = min(max(elapsed_minutes, 60), 1440) 

    try:
        # ใช้ Exchange 'OANDA' หรือ 'FX_IDC' ขึ้นอยู่กับคู่เงิน (OANDA รองรับคู่หลักส่วนใหญ่)
        init_rates = tv.get_hist(symbol=pair_symbol, exchange='OANDA', interval=Interval.in_1_minute, n_bars=init_bars)
        if init_rates is not None and not init_rates.empty:
            init_rates.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
            init_rates = init_rates.iloc[:-1] # ตัดแท่งปัจจุบันที่ยังวิ่งไม่เสร็จออก ป้องกันข้อมูลซ้อน
            
            df_live = init_rates[['Open', 'High', 'Low', 'Close']].copy()
            
            for index, row in init_rates.iterrows():
                timestamp_seconds = int(index.timestamp())
                candle_payload = {
                    "type": "CANDLE",
                    "data": {
                        "time": timestamp_seconds,
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close'])
                    }
                }
                await manager.broadcast(json.dumps(candle_payload))
                await asyncio.sleep(0.0005)
                
            print(f"✅ [LIVE] ปูพื้นกระดาน {display_name} สำเร็จแล้ว เริ่มสตรีมราคาปัจจุบัน...")
    except Exception as e:
        print(f"⚠️ [LIVE] ไม่สามารถดึงข้อมูลตั้งต้นได้: {e}")
        df_live = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close'])

    last_processed_time = None

    while True:
        try:
            rates = tv.get_hist(symbol=pair_symbol, exchange='OANDA', interval=Interval.in_1_minute, n_bars=2)
            if rates is not None and not rates.empty:
                rates.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
                
                for index, row in rates.iterrows():
                    timestamp_seconds = int(index.timestamp())
                    candle_payload = {
                        "type": "CANDLE",
                        "data": {"time": timestamp_seconds, "open": float(row['Open']), "high": float(row['High']), "low": float(row['Low']), "close": float(row['Close'])}
                    }
                    await manager.broadcast(json.dumps(candle_payload))

                latest_stable_time = rates.index[-2]
                if latest_stable_time != last_processed_time:
                    stable_row = rates.loc[latest_stable_time]
                    new_candle = {'Open': float(stable_row['Open']), 'High': float(stable_row['High']), 'Low': float(stable_row['Low']), 'Close': float(stable_row['Close'])}
                    df_live.loc[len(df_live)] = new_candle
                    
                    if len(df_live) > 50:
                        df_live = df_live.tail(50).reset_index(drop=True)
                    
                    signal = analyzer.analyze_candle(df_live, ticker=display_name)
                    if signal:
                        human_time = latest_stable_time.strftime('%H:%M')
                        signal_payload = {
                            "type": "SIGNAL",
                            "data": {
                                "id": int(time.time()), 
                                "timestamp": human_time, 
                                "raw_time": int(latest_stable_time.timestamp()), 
                                "underlying": display_name, 
                                "option_type": signal['option_type'], 
                                "strike": round(float(stable_row['Close']), 5), 
                                "result": "LIVE"
                            }
                        }
                        await manager.broadcast(json.dumps(signal_payload))
                    last_processed_time = latest_stable_time
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(5)

@router.post("/live/start")
async def start_live_stream(symbol: str = Query("EURUSD")):
    global live_streaming_task
    if live_streaming_task and not live_streaming_task.done():
        return {"status": "success", "message": "Live stream already running"}
    
    # ส่งพารามิเตอร์คู่เงินเข้าท่อสตรีมเบื้องหลัง
    live_streaming_task = asyncio.create_task(stream_live_market_data(symbol))
    return {"status": "success", "message": f"Live stream for {symbol} started"}

@router.post("/live/stop")
async def stop_live_stream():
    global live_streaming_task
    if live_streaming_task:
        live_streaming_task.cancel()
        live_streaming_task = None
        return {"status": "success", "message": "Live stream stopped"}
    return {"status": "success", "message": "Live stream is not running"}

@router.post("/backtest/run")
async def run_visual_backtest(symbol: str = Query("EURUSD")):
    pair_symbol = symbol
    display_name = f"{pair_symbol[:3]}/{pair_symbol[3:]}" if len(pair_symbol) == 6 else pair_symbol
    
    print(f"⏳ [BACKTEST] กำลังดึงข้อมูลอดีตของคู่เงิน {display_name}...")
    try:
        tv = TvDatafeed() 
        rates = tv.get_hist(symbol=pair_symbol, exchange='OANDA', interval=Interval.in_1_minute, n_bars=1000)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    if rates is None or len(rates) == 0:
        return {"status": "error", "message": "ไม่พบข้อมูลอดีต"}
        
    hist = rates.copy()
    hist.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
    hist_len = len(hist)
    expiry_candles = 5
    
    analyzer = SMA4Analyzer()
    df = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close'])
    
    for i in range(hist_len):
        try:
            row = hist.iloc[i]
            timestamp_seconds = int(hist.index[i].timestamp())
            o_val = float(row['Open'])
            h_val = float(row['High'])
            l_val = float(row['Low'])
            c_val = float(row['Close'])

            candle_payload = {
                "type": "CANDLE",
                "data": {"time": timestamp_seconds, "open": o_val, "high": h_val, "low": l_val, "close": c_val}
            }
            await manager.broadcast(json.dumps(candle_payload))

            new_candle = {'Open': o_val, 'High': h_val, 'Low': l_val, 'Close': c_val}
            df.loc[len(df)] = new_candle
            
            if len(df) > 50: 
                df = df.tail(50).reset_index(drop=True)
                
            signal = analyzer.analyze_candle(df, ticker=display_name)
            if signal:
                strike_price = c_val
                trade_result = "LOSS"
                if i + expiry_candles < hist_len:
                    future_close = float(hist.iloc[i + expiry_candles]['Close'])
                    if signal['option_type'] == 'CALL' and future_close > strike_price: trade_result = "WIN"
                    elif signal['option_type'] == 'PUT' and future_close < strike_price: trade_result = "WIN"

                human_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(timestamp_seconds))
                signal_payload = {
                    "type": "SIGNAL",
                    "data": {
                        "id": int(time.time()) + timestamp_seconds, 
                        "timestamp": human_time, 
                        "raw_time": timestamp_seconds, 
                        "underlying": display_name, 
                        "option_type": signal['option_type'], 
                        "strike": round(strike_price, 5), 
                        "result": trade_result
                    }
                }
                await manager.broadcast(json.dumps(signal_payload))
            await asyncio.sleep(0.001)
        except Exception:
            continue
    return {"status": "success", "message": "Backtest finished"}

@router.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)