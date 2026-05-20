71.4

import pandas as pd

class SMA4Analyzer:
    def __init__(self):
        self.sma_period = 4
        self.sr_period = 20  # มองย้อนหลัง 20 แท่งเพื่อหาแนวรับแนวต้าน

    def analyze_candle(self, df, ticker="Asset"):
        if len(df) < self.sr_period:
            return None
            
        # 1. คำนวณ SMA4 และ แนวรับ/แนวต้าน
        df['SMA4'] = df['Close'].rolling(window=self.sma_period).mean()
        df['Resistance'] = df['High'].shift(1).rolling(window=self.sr_period).max()
        df['Support'] = df['Low'].shift(1).rolling(window=self.sr_period).min()

        curr_candle = df.iloc[-1]

        if pd.isna(curr_candle['SMA4']) or pd.isna(curr_candle['Resistance']):
            return None

        # 🔥 ด่านที่ 1: เช็คความสมบูรณ์ของแท่งเทียน (Solid Candle >= 70%)
        body_size = abs(curr_candle['Open'] - curr_candle['Close'])
        total_size = curr_candle['High'] - curr_candle['Low']
        
        if total_size == 0 or body_size == 0: 
            return None # ป้องกันหาร 0 และแท่งขีด
            
        body_ratio = body_size / total_size
        is_solid_candle = body_ratio >= 0.70

        # ถ้าแท่งเทียนมีไส้ยาวเกินไป (เนื้อไม่ถึง 70%) ให้ปัดตกทันที ไม่ต้องคำนวณต่อ
        if not is_solid_candle:
            return None

        cross_up = False
        cross_down = False

        # 🔥 ด่านที่ 2: เงื่อนไขจุดตัดต้นน้ำ (Early Breakout ตัดไม่เกิน 30% แรก)
        # CALL (ซื้อขึ้น): ราคาเปิดต่ำกว่าเส้น SMA และราคาปิดทะลุเหนือเส้น
        if curr_candle['Open'] < curr_candle['SMA4'] < curr_candle['Close']:
            cut_ratio = (curr_candle['SMA4'] - curr_candle['Open']) / body_size
            if cut_ratio <= 0.3:
                cross_up = True
                
        # PUT (ซื้อลง): ราคาเปิดสูงกว่าเส้น SMA และราคาปิดมุดใต้เส้น
        elif curr_candle['Open'] > curr_candle['SMA4'] > curr_candle['Close']:
            cut_ratio = (curr_candle['Open'] - curr_candle['SMA4']) / body_size
            if cut_ratio <= 0.3:
                cross_down = True

        # 🔥 ด่านที่ 3: ตัวกรองแนวรับแนวต้าน (Support/Resistance Squeeze)
        channel_range = curr_candle['Resistance'] - curr_candle['Support']
        if channel_range == 0:
            return None 
            
        # หาว่าราคาปัจจุบันอยู่ส่วนไหนของกรอบ (0.0 = ติดพื้นแนวรับ, 1.0 = ติดเพดานแนวต้าน)
        price_position = (curr_candle['Close'] - curr_candle['Support']) / channel_range

        signal_type = None

        # เงื่อนไข CALL ขั้นสุดยอด: แท่งตัน + ตัดต้นเทรนด์ + อยู่ครึ่งล่างใกล้แนวรับ
        if cross_up and price_position <= 0.5:
            signal_type = 'CALL'
        
        # เงื่อนไข PUT ขั้นสุดยอด: แท่งตัน + ตัดต้นเทรนด์ + อยู่ครึ่งบนใกล้แนวต้าน
        elif cross_down and price_position >= 0.5:
            signal_type = 'PUT'

        if signal_type:
            return {
                'option_type': signal_type,
                'close_price': curr_candle['Close']
            }
        
        return None
