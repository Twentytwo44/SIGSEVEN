import pandas as pd

class SMA4Analyzer:
    def __init__(self):
        self.sma_period = 4
        self.sr_period = 20  # มองย้อนหลัง 20 แท่งเพื่อหาแนวรับแนวต้าน

    def analyze_candle(self, df, ticker="Asset"):
        if len(df) < self.sr_period:
            return None
            
        # 1. คำนวณ SMA4, แนวรับ/แนวต้าน และ ขนาดแท่งเทียนเฉลี่ย
        df['SMA4'] = df['Close'].rolling(window=self.sma_period).mean()
        df['Resistance'] = df['High'].shift(1).rolling(window=self.sr_period).max()
        df['Support'] = df['Low'].shift(1).rolling(window=self.sr_period).min()
        
        df['Total_Size'] = df['High'] - df['Low']
        df['Avg_Size'] = df['Total_Size'].shift(1).rolling(window=self.sr_period).mean()

        prev_candle = df.iloc[-2]
        curr_candle = df.iloc[-1]

        if pd.isna(curr_candle['SMA4']) or pd.isna(prev_candle['SMA4']) or pd.isna(curr_candle['Resistance']) or pd.isna(curr_candle['Avg_Size']):
            return None

        # ด่านพิเศษ: กรองแท่งเทียนขนาดจิ๋ว (Micro-Candle Noise)
        if curr_candle['Total_Size'] < (curr_candle['Avg_Size'] * 0.6):
            return None

        # 2. ตัวกรองความสมบูรณ์ของแท่งเทียน (Solid Candle ล็อกแน่นๆ ที่ 70%)
        body_size = abs(curr_candle['Open'] - curr_candle['Close'])
        if body_size == 0: 
            return None 
            
        body_ratio = body_size / curr_candle['Total_Size']
        is_solid_candle = body_ratio >= 0.70  

        if not is_solid_candle:
            return None

        cross_up = False
        cross_down = False

        # 🔥 3. ลอจิกจุดตัดซ้าย-ขวา แบบล็อกขอบเขต (ป้องกันบั๊กค่าติดลบ)
        
        # 🟢 เคส CALL (แท่งเขียว)
        if curr_candle['Close'] > curr_candle['Open']:
            left_cut = (prev_candle['SMA4'] - curr_candle['Open']) / body_size
            right_cut = (curr_candle['SMA4'] - curr_candle['Open']) / body_size
            
            # 💡 [FIX] เพิ่ม 0.0 <= เพื่อบังคับให้เส้นต้องตัดเข้าไปในเนื้อเทียนจริงเท่านั้น ไม่ใช่ลอยอยู่ข้างล่าง
            if (0.0 <= left_cut <= 0.20) and (right_cut > left_cut) and (right_cut <= 0.40):
                cross_up = True

        # 🔴 เคส PUT (แท่งแดง)
        elif curr_candle['Open'] > curr_candle['Close']:
            left_cut = (curr_candle['Open'] - prev_candle['SMA4']) / body_size
            right_cut = (curr_candle['Open'] - curr_candle['SMA4']) / body_size
            
            # 💡 [FIX] เพิ่ม 0.0 <= บังคับให้เส้นต้องตัดเฉือนจากขอบบนเข้าเนื้อแท่งแดงจริงๆ ไม่ใช่ลอยอยู่ข้างบน
            if (0.0 <= left_cut <= 0.20) and (right_cut > left_cut) and (right_cut <= 0.40):
                cross_down = True

        # 4. ตัวกรองแนวรับแนวต้าน (Support/Resistance Squeeze)
        channel_range = curr_candle['Resistance'] - curr_candle['Support']
        if channel_range == 0:
            return None 
            
        price_position = (curr_candle['Close'] - curr_candle['Support']) / channel_range

        signal_type = None

        if cross_up and price_position <= 0.8:
            signal_type = 'CALL'
        elif cross_down and price_position >= 0.2:
            signal_type = 'PUT'

        if signal_type:
            return {
                'option_type': signal_type,
                'close_price': curr_candle['Close']
            }
        
        return None