# import pandas as pd

# class SMA4Analyzer:
#     def __init__(self):
#         self.sma_period = 4
#         self.sr_period = 20  # มองย้อนหลัง 20 แท่งเพื่อหาแนวรับแนวต้าน

#     def analyze_candle(self, df, ticker="Asset"):
#         if len(df) < self.sr_period:
#             return None
            
#         # 1. คำนวณ SMA4, แนวรับ/แนวต้าน และ ขนาดแท่งเทียนเฉลี่ย
#         df['SMA4'] = df['Close'].rolling(window=self.sma_period).mean()
#         df['Resistance'] = df['High'].shift(1).rolling(window=self.sr_period).max()
#         df['Support'] = df['Low'].shift(1).rolling(window=self.sr_period).min()
        
#         df['Total_Size'] = df['High'] - df['Low']
#         df['Avg_Size'] = df['Total_Size'].shift(1).rolling(window=self.sr_period).mean()

#         prev_candle = df.iloc[-2]
#         curr_candle = df.iloc[-1]

#         if pd.isna(curr_candle['SMA4']) or pd.isna(prev_candle['SMA4']) or pd.isna(curr_candle['Resistance']) or pd.isna(curr_candle['Avg_Size']):
#             return None

#         # ด่านพิเศษ: กรองแท่งเทียนขนาดจิ๋ว (Micro-Candle Noise)
#         if curr_candle['Total_Size'] < (curr_candle['Avg_Size'] * 0.6):
#             return None

#         # 2. ตัวกรองความสมบูรณ์ของแท่งเทียน (Solid Candle ล็อกแน่นๆ ที่ 70%)
#         body_size = abs(curr_candle['Open'] - curr_candle['Close'])
#         if body_size == 0: 
#             return None 
            
#         body_ratio = body_size / curr_candle['Total_Size']
#         is_solid_candle = body_ratio >= 0.70  

#         if not is_solid_candle:
#             return None

#         cross_up = False
#         cross_down = False

#         # 🔥 3. ลอจิกจุดตัดซ้าย-ขวา แบบล็อกขอบเขต (ป้องกันบั๊กค่าติดลบ)
        
#         # 🟢 เคส CALL (แท่งเขียว)
#         if curr_candle['Close'] > curr_candle['Open']:
#             left_cut = (prev_candle['SMA4'] - curr_candle['Open']) / body_size
#             right_cut = (curr_candle['SMA4'] - curr_candle['Open']) / body_size
            
#             # 💡 [FIX] เพิ่ม 0.0 <= เพื่อบังคับให้เส้นต้องตัดเข้าไปในเนื้อเทียนจริงเท่านั้น ไม่ใช่ลอยอยู่ข้างล่าง
#             if (0.0 <= left_cut <= 0.20) and (right_cut > left_cut) and (right_cut <= 0.40):
#                 cross_up = True

#         # 🔴 เคส PUT (แท่งแดง)
#         elif curr_candle['Open'] > curr_candle['Close']:
#             left_cut = (curr_candle['Open'] - prev_candle['SMA4']) / body_size
#             right_cut = (curr_candle['Open'] - curr_candle['SMA4']) / body_size
            
#             # 💡 [FIX] เพิ่ม 0.0 <= บังคับให้เส้นต้องตัดเฉือนจากขอบบนเข้าเนื้อแท่งแดงจริงๆ ไม่ใช่ลอยอยู่ข้างบน
#             if (0.0 <= left_cut <= 0.20) and (right_cut > left_cut) and (right_cut <= 0.40):
#                 cross_down = True

#         # 4. ตัวกรองแนวรับแนวต้าน (Support/Resistance Squeeze)
#         channel_range = curr_candle['Resistance'] - curr_candle['Support']
#         if channel_range == 0:
#             return None 
            
#         price_position = (curr_candle['Close'] - curr_candle['Support']) / channel_range

#         signal_type = None

#         if cross_up and price_position <= 0.8:
#             signal_type = 'CALL'
#         elif cross_down and price_position >= 0.2:
#             signal_type = 'PUT'

#         if signal_type:
#             return {
#                 'option_type': signal_type,
#                 'close_price': curr_candle['Close']
#             }
        
#         return None



import pandas as pd
import numpy as np

class EnhancedSMAAnalyzer:
    def __init__(self):
        # --- พารามิเตอร์ดั้งเดิม ---
        self.sma_period = 4
        self.sr_period = 20  
        
        # --- 🌟 พารามิเตอร์ระดับโปร (เพิ่มเข้ามาใหม่) ---
        self.ema_trend = 50  # ใช้บอกเทรนด์หลัก (ห้ามเทรดสวนเทรนด์นี้)
        self.rsi_period = 14 # ใช้บอกว่ากราฟมีแรงวิ่งต่อไหม (โมเมนตัม)

    def _calculate_rsi(self, series, period):
        """คำนวณ RSI แบบมาตรฐาน (เทียบเท่า TradingView)"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def analyze_candle(self, df, ticker="Asset"):
        # รอให้แท่งเทียนมีมากพอสำหรับคำนวณ EMA50
        if len(df) < self.ema_trend:
            return None
            
        # 1. คำนวณ Indicators (เดิม + ใหม่)
        df['SMA4'] = df['Close'].rolling(window=self.sma_period).mean()
        df['Resistance'] = df['High'].shift(1).rolling(window=self.sr_period).max()
        df['Support'] = df['Low'].shift(1).rolling(window=self.sr_period).min()
        
        df['Total_Size'] = df['High'] - df['Low']
        df['Avg_Size'] = df['Total_Size'].shift(1).rolling(window=self.sr_period).mean()
        
        # 🌟 ตัวกรองใหม่
        df['EMA50'] = df['Close'].ewm(span=self.ema_trend, adjust=False).mean()
        df['RSI'] = self._calculate_rsi(df['Close'], self.rsi_period)

        prev_candle = df.iloc[-2]
        curr_candle = df.iloc[-1]

        if pd.isna(curr_candle['SMA4']) or pd.isna(curr_candle['EMA50']) or pd.isna(curr_candle['RSI']):
            return None

        # 2. ด่านพิเศษ: กรองแท่งเทียนจิ๋ว (Micro-Candle Noise)
        if curr_candle['Total_Size'] < (curr_candle['Avg_Size'] * 0.6):
            return None

        # 3. ตัวกรองความสมบูรณ์ของแท่งเทียน (Solid Candle ล็อกแน่นๆ ที่ 70%)
        body_size = abs(curr_candle['Open'] - curr_candle['Close'])
        if body_size == 0: 
            return None 
            
        body_ratio = body_size / curr_candle['Total_Size']
        if body_ratio < 0.70:
            return None

        cross_up = False
        cross_down = False

        # 🔥 4. ลอจิกจุดตัดซ้าย-ขวา แบบล็อกขอบเขต (โค้ดสุดเฉียบของพี่)
        if curr_candle['Close'] > curr_candle['Open']: # แท่งเขียว
            left_cut = (prev_candle['SMA4'] - curr_candle['Open']) / body_size
            right_cut = (curr_candle['SMA4'] - curr_candle['Open']) / body_size
            
            if (0.0 <= left_cut <= 0.20) and (right_cut > left_cut) and (right_cut <= 0.40):
                cross_up = True

        elif curr_candle['Open'] > curr_candle['Close']: # แท่งแดง
            left_cut = (curr_candle['Open'] - prev_candle['SMA4']) / body_size
            right_cut = (curr_candle['Open'] - curr_candle['SMA4']) / body_size
            
            if (0.0 <= left_cut <= 0.20) and (right_cut > left_cut) and (right_cut <= 0.40):
                cross_down = True

        # 5. ตัวกรองแนวรับแนวต้าน (Support/Resistance Squeeze)
        channel_range = curr_candle['Resistance'] - curr_candle['Support']
        if channel_range == 0:
            return None 
            
        price_position = (curr_candle['Close'] - curr_candle['Support']) / channel_range

        signal_type = None

        # 🌟 6. ลอจิกตัดสินใจขั้นสุดท้าย (ผนวก Trend + Momentum)
        # เงื่อนไข CALL:
        # - SMA4 ตัดเนื้อเทียนสวยงาม (ลอจิกพี่)
        # - ราคาไม่ชนแนวต้าน (ลอจิกพี่)
        # - ราคาปิดยืนเหนือ EMA50 (แปลว่าเทรนด์หลักยังเป็นขาขึ้น ไม่ได้สวนทาง)
        # - RSI อยู่ระหว่าง 50 ถึง 70 (มีแรงซื้อหนุนหลัง แต่ยังไม่ Overbought จนเสี่ยงดอย)
        if cross_up and price_position <= 0.8:
            if curr_candle['Close'] > curr_candle['EMA50'] and (50 < curr_candle['RSI'] < 70):
                signal_type = 'CALL'

        # เงื่อนไข PUT:
        # - SMA4 ตัดเนื้อแท่งแดงสวยงาม
        # - ราคาไม่ติดแนวรับ
        # - ราคาปิดอยู่ใต้ EMA50 (เทรนด์หลักเป็นขาลงชัดเจน)
        # - RSI อยู่ระหว่าง 30 ถึง 50 (มีแรงขายกดดันต่อเนื่อง แต่ยังไม่ Oversold)
        elif cross_down and price_position >= 0.2:
            if curr_candle['Close'] < curr_candle['EMA50'] and (30 < curr_candle['RSI'] < 50):
                signal_type = 'PUT'

        if signal_type:
            return {
                'option_type': signal_type,
                'close_price': curr_candle['Close'],
                'rsi_momentum': round(curr_candle['RSI'], 2),
                'trend_confirmed': True
            }
        
        return None