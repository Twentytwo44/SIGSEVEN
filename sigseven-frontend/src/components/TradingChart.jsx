import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const TradingChart = () => {
  const chartContainerRef = useRef();

  useEffect(() => {
    // 1. สร้างตัวกราฟและตั้งค่าสีให้เข้ากับธีม Dark Mode ของเรา
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#D1D5DB',
      },
      grid: {
        vertLines: { color: '#374151', style: 1 },
        horzLines: { color: '#374151', style: 1 },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // 2. สร้างกราฟแท่งเทียน (Candlestick)
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    // 3. ใส่ข้อมูลจำลอง (เดี๋ยวพอต่อ API จริง เราจะส่งข้อมูลจาก Backend มาใส่ตรงนี้)
    const mockData = [];
    let time = Math.floor(Date.now() / 1000) - 86400; // เริ่มจากเมื่อวาน
    let price = 500;
    
    for (let i = 0; i < 100; i++) {
      time += 60; // เพิ่มทีละ 1 นาที
      const open = price + (Math.random() - 0.5) * 2;
      const close = open + (Math.random() - 0.5) * 2;
      const high = Math.max(open, close) + Math.random();
      const low = Math.min(open, close) - Math.random();
      mockData.push({ time, open, high, low, close });
      price = close;
    }
    
    candlestickSeries.setData(mockData);
    chart.timeScale().fitContent();

    // 4. ทำให้กราฟย่อขยายตามหน้าจอ (Responsive)
    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  return (
    <div className="w-full h-[400px] bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl overflow-hidden shadow-lg p-4">
        <h2 className="text-gray-400 text-sm font-semibold mb-2">SPY (S&P 500) - 1 Minute (Mock View)</h2>
        <div ref={chartContainerRef} className="w-full h-[340px]" />
    </div>
  );
};

export default TradingChart;