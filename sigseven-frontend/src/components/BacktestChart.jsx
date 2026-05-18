import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export default function BacktestChart({ candleData = [], signals = [], isLive = false }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const smaLineSeriesRef = useRef(null);
  const resLineSeriesRef = useRef(null);
  const supLineSeriesRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: { background: { color: '#0f172a' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      timeScale: { timeVisible: true, secondsVisible: false, rightOffset: 5 },
      rightPriceScale: { autoScale: true, alignLabels: true },
      localization: { priceFormatter: (price) => price.toFixed(5) },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#10b981', downColor: '#ef4444', borderVisible: false,
      wickUpColor: '#10b981', wickDownColor: '#ef4444',
      priceFormat: { type: 'price', precision: 5, minMove: 0.00001 },
    });

    const smaLineSeries = chart.addLineSeries({
      color: '#3b82f6', lineWidth: 2, crosshairMarkerVisible: false, priceLineVisible: false,
    });

    // 🔥 เส้นแนวต้านสีแดงประ
    const resLineSeries = chart.addLineSeries({
      color: 'rgba(239, 68, 68, 0.5)', lineWidth: 1, lineStyle: 2, crosshairMarkerVisible: false, priceLineVisible: false,
    });

    // 🔥 เส้นแนวรับสีเขียวประ
    const supLineSeries = chart.addLineSeries({
      color: 'rgba(16, 185, 129, 0.5)', lineWidth: 1, lineStyle: 2, crosshairMarkerVisible: false, priceLineVisible: false,
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    smaLineSeriesRef.current = smaLineSeries;
    resLineSeriesRef.current = resLineSeries;
    supLineSeriesRef.current = supLineSeries;

    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!candlestickSeriesRef.current || candleData.length === 0) return;

    try {
      const uniqueCandles = [...candleData]
        .filter((v, i, a) => a.findIndex(t => (t.time === v.time)) === i)
        .sort((a, b) => a.time - b.time);

      candlestickSeriesRef.current.setData(uniqueCandles);

      const smaData = [];
      const resData = [];
      const supData = [];
      
      for (let i = 0; i < uniqueCandles.length; i++) {
        // คำนวณ SMA4
        if (i >= 3) {
          const sum = uniqueCandles[i].close + uniqueCandles[i-1].close + uniqueCandles[i-2].close + uniqueCandles[i-3].close;
          smaData.push({ time: uniqueCandles[i].time, value: sum / 4 });
        }
        
        // คำนวณแนวรับ/ต้าน ย้อนหลัง 20 แท่ง
        if (i >= 20) {
          let maxH = uniqueCandles[i-1].high;
          let minL = uniqueCandles[i-1].low;
          for (let j = 1; j <= 20; j++) {
            if (uniqueCandles[i-j].high > maxH) maxH = uniqueCandles[i-j].high;
            if (uniqueCandles[i-j].low < minL) minL = uniqueCandles[i-j].low;
          }
          resData.push({ time: uniqueCandles[i].time, value: maxH });
          supData.push({ time: uniqueCandles[i].time, value: minL });
        }
      }
      
      smaLineSeriesRef.current.setData(smaData);
      resLineSeriesRef.current.setData(resData);
      supLineSeriesRef.current.setData(supData);

      // 🔥 การจัดการซูม
      if (chartRef.current) {
        const timeScale = chartRef.current.timeScale();
        const total = uniqueCandles.length;
        const logicalRange = timeScale.getVisibleLogicalRange();

        if (!logicalRange || (!isLive && total > 0)) {
          // โหลดครั้งแรก หรือ Backtest ให้พอดีจอ
          if (total > 150) timeScale.setVisibleLogicalRange({ from: total - 150, to: total - 1 });
          else timeScale.fitContent();
        } else if (isLive && logicalRange) {
           // Live Mode: ถ้าผู้ใช้อยู่หน้าสุด ค่อยเลื่อนตาม ไม่งั้นปล่อยซูมอิสระ
           const isAtEnd = logicalRange.to >= (total - 5);
           if (isAtEnd) {
             const rangeSize = logicalRange.to - logicalRange.from;
             timeScale.setVisibleLogicalRange({ from: total - rangeSize, to: total - 1 });
           }
        }
      }
    } catch (error) {
      console.error("Error drawing chart:", error);
    }
  }, [candleData, isLive]);

  useEffect(() => {
    if (!candlestickSeriesRef.current || signals.length === 0 || candleData.length === 0) return;

    try {
      const markers = signals
        .map((sig) => ({
          time: sig.raw_time,
          position: sig.option_type === 'CALL' ? 'belowBar' : 'aboveBar',
          color: sig.option_type === 'CALL' ? '#10b981' : '#ef4444',
          shape: sig.option_type === 'CALL' ? 'arrowUp' : 'arrowDown',
          text: sig.option_type,
        }))
        .filter(m => candleData.some(c => c.time === m.time))
        .sort((a, b) => a.time - b.time); 

      candlestickSeriesRef.current.setMarkers(markers);
    } catch (error) {
      console.error("Error setting markers:", error);
    }
  }, [signals, candleData]);

  return <div ref={chartContainerRef} className="w-full h-full rounded-lg" />;
}