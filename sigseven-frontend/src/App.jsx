import React, { useState, useEffect } from 'react';
import BacktestChart from './components/BacktestChart';

export default function App() {
  const [candles, setCandles] = useState([]);
  const [signals, setSignals] = useState([]);
  const [isTesting, setIsTesting] = useState(false);
  const [isLive, setIsLive] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Standby');
  
  // 🔥 สเตตสำหรับเก็บคู่เงินที่เลือก (Default: EURUSD)
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');

  // รายชื่อคู่เงินที่ต้องการให้เลือกเทรดได้
  const assetPairs = [
    { code: 'EURUSD', name: 'EUR/USD' },
    { code: 'GBPUSD', name: 'GBP/USD' },
    { code: 'USDJPY', name: 'USD/JPY' },
    { code: 'AUDUSD', name: 'AUD/USD' },
    { code: 'USDCAD', name: 'USD/CAD' }
  ];

  const handleReset = async () => {
    if (isLive) {
      await fetch('http://localhost:8000/live/stop', { method: 'POST' });
      setIsLive(false);
    }
    setCandles([]);
    setSignals([]);
    setIsTesting(false);
    setStatusMessage('Dashboard Reset Complete');
  };

  const handleRunBacktest = async () => {
    if (isLive) await handleReset();
    setIsTesting(true);
    setStatusMessage(`Fetching historical data for ${selectedSymbol}...`);
    setCandles([]); setSignals([]); 

    try {
      // 🔥 แนบคู่เงินไปกับ Query String
      const response = await fetch(`http://localhost:8000/backtest/run?symbol=${selectedSymbol}`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') setStatusMessage('Backtest processed successfully!');
      else { alert(`Error: ${data.message}`); setIsTesting(false); }
    } catch (error) {
      alert("เชื่อมต่อ Backend ไม่สำเร็จ");
      setIsTesting(false);
    }
  };

  const handleToggleLive = async () => {
    // ส่งสัญลักษณ์คู่เงินไปด้วยตอนกดเริ่มสตรีมราคา
    const endpoint = isLive ? 'stop' : `start?symbol=${selectedSymbol}`;
    try {
      const response = await fetch(`http://localhost:8000/live/${endpoint}`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') {
        setIsLive(!isLive);
        setStatusMessage(isLive ? 'Live Stopped' : `🔴 ${selectedSymbol} is streaming live...`);
        if (!isLive) {
          setCandles([]); setSignals([]);
        }
      }
    } catch (error) {
      alert("ไม่สามารถเปลี่ยนโหมดเรียลไทม์ได้");
    }
  };

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/signals');
    let candleBuffer = []; 
    let flushTimeout = null;

    const flushBuffer = () => {
      if (candleBuffer.length > 0) {
        const currentBuffer = [...candleBuffer];
        candleBuffer = []; 
        setCandles((prev) => {
          const candleMap = new Map(prev.map(c => [c.time, c]));
          currentBuffer.forEach(c => candleMap.set(c.time, c));
          return Array.from(candleMap.values()).sort((a, b) => a.time - b.time);
        });
      }
    };

    ws.onmessage = (event) => {
      try {
        let response = JSON.parse(event.data);
        if (typeof response === 'string') response = JSON.parse(response);
        
        if (response.type === 'CANDLE') {
          candleBuffer.push(response.data);
          if (flushTimeout) clearTimeout(flushTimeout);
          if (candleBuffer.length >= 50) flushBuffer();
          else flushTimeout = setTimeout(flushBuffer, 50);
        } 
        else if (response.type === 'SIGNAL') {
          setSignals((prev) => [response.data, ...prev]);
        }
      } catch (err) {}
    };

    return () => {
      if (flushTimeout) clearTimeout(flushTimeout);
      ws.close();
    };
  }, []);

  const totalSignals = signals.length;
  const winCount = signals.filter(sig => sig.result === 'WIN').length;
  const lossCount = signals.filter(sig => sig.result === 'LOSS').length;
  const winRate = totalSignals > 0 ? ((winCount / totalSignals) * 100).toFixed(1) : 0.0;

  return (
    <div className="p-6 bg-slate-950 text-white min-h-screen font-sans">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6 bg-slate-900 p-4 rounded-xl border border-slate-800 shadow-xl">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-indigo-400">SIGSEVEN Options Engine</h1>
          <p className="text-xs text-slate-400 mt-1">Status: <span className={isLive ? "text-rose-500 font-bold" : "text-emerald-400"}>{statusMessage}</span></p>
        </div>

        <div className="hidden md:flex gap-4 items-center bg-slate-950 p-2 px-6 rounded-lg border border-slate-800 shadow-inner">
          <div><p className="text-[10px] text-slate-500 font-bold text-center">TOTAL</p><p className="text-lg font-mono font-bold text-slate-200 text-center">{totalSignals}</p></div>
          <div className="w-px h-8 bg-slate-800 mx-2"></div>
          <div><p className="text-[10px] text-emerald-500 font-bold text-center">WINS</p><p className="text-lg font-mono font-bold text-emerald-400 text-center">{winCount}</p></div>
          <div><p className="text-[10px] text-rose-500 font-bold text-center">LOSSES</p><p className="text-lg font-mono font-bold text-rose-400 text-center">{lossCount}</p></div>
          <div className="bg-indigo-500/10 px-4 py-1.5 rounded border border-indigo-500/20 ml-2">
            <p className="text-[10px] text-indigo-400 font-bold tracking-wider">WIN RATE</p>
            <p className="text-lg font-mono font-bold text-indigo-300">{winRate}%</p>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-4 items-center w-full lg:w-auto justify-end">
          
          {/* 🔥 กล่องเลือกคู่เงินเพิ่มเข้ามาตรงนี้ */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg">
            <label className="text-xs text-slate-500 font-bold">ASSET:</label>
            <select 
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              disabled={isTesting || isLive} // ล็อกห้ามเปลี่ยนคู่เงินขณะรันงานอยู่
              className="bg-transparent text-sm font-semibold text-indigo-400 focus:outline-none cursor-pointer disabled:opacity-50"
            >
              {assetPairs.map((pair) => (
                <option key={pair.code} value={pair.code} className="bg-slate-900 text-white">{pair.name}</option>
              ))}
            </select>
          </div>

          {(candles.length > 0 || signals.length > 0) && (
            <button onClick={handleReset} className="px-4 py-2.5 bg-slate-800 hover:bg-rose-900/30 text-rose-400 border border-slate-700 rounded-lg text-sm font-semibold transition-all">
              Reset
            </button>
          )}

          <button onClick={handleToggleLive} disabled={isTesting} className={`px-5 py-2.5 rounded-lg font-semibold text-sm transition-all shadow-md ${isLive ? 'bg-rose-600 text-white animate-pulse' : 'bg-slate-800 text-slate-200 border border-slate-700'}`}>
            {isLive ? '🛑 Stop Live' : '📡 Go Live (Realtime)'}
          </button>

          <button onClick={handleRunBacktest} disabled={isTesting || isLive} className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg font-semibold text-sm shadow-md">
            {isTesting ? '⏳ Processing...' : '▶ Run Backtest'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 p-4 rounded-xl border border-slate-800 h-[600px] shadow-xl flex flex-col">
          <h2 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-rose-500 animate-ping' : 'bg-emerald-500'}`}></span>
VISUAL CHART: {selectedSymbol.slice(0, 3)}/{selectedSymbol.slice(3)} (1m) {isLive && "• LIVE"}          </h2>
          <div className="flex-1 w-full bg-slate-950 rounded-lg overflow-hidden relative border border-slate-850">
            {candles.length === 0 ? (
              <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-sm">กระดานว่างเปล่า กรุณาเลือกคู่เงินแล้วกดปุ่มด้านบน</div>
            ) : (
              <BacktestChart candleData={candles} signals={signals} isLive={isLive} />
            )}
          </div>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 h-[600px] shadow-xl flex flex-col">
          <h2 className="text-sm font-semibold text-slate-400 mb-3">🚨 LOGGED OPTIONS SIGNALS</h2>
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 scrollbar-thin scrollbar-thumb-slate-800">
            {signals.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-sm gap-2">No signals captured yet.</div>
            ) : (
              signals.map((sig) => (
                <div key={sig.id + Math.random()} className={`p-3 rounded-lg border transition-all duration-300 ${sig.option_type === 'CALL' ? 'bg-emerald-950/30 border-emerald-500/20 text-emerald-200' : 'bg-rose-950/30 border-rose-500/20 text-rose-200'}`}>
                  <div className="flex justify-between items-center mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${sig.option_type === 'CALL' ? 'bg-emerald-500 text-white' : 'bg-rose-500 text-white'}`}>{sig.option_type}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${sig.result === 'WIN' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50' : sig.result === 'LOSS' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/50' : 'bg-slate-700 text-slate-300'}`}>{sig.result || 'WAITING'}</span>
                    </div>
                    <span className="text-xs font-mono text-slate-400">{sig.timestamp}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-y-1 text-xs font-mono mt-2 pt-2 border-t border-slate-800/60">
                    <div className="text-slate-400">Asset:</div><div className="text-right text-white font-semibold">{sig.underlying}</div>
                    <div className="text-slate-400">Strike Target:</div><div className="text-right text-white font-semibold">{sig.strike?.toFixed(5)}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}