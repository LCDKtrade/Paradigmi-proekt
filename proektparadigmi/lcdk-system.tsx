"use client";
import { useEffect, useState } from 'react';

export default function Home() {
  const [signals, setSignals] = useState<any[]>([]);
  const [status, setStatus] = useState("Connecting to LCDK Engine...");

  useEffect(() => {
    // Се поврзуваме со Python Backend-от на порта 8000
    const ws = new WebSocket('ws://localhost:8000/ws/signals');
    
    ws.onopen = () => setStatus("LIVE: AI Signals Active");
    
    ws.onmessage = (event) => {
      const newSignal = JSON.parse(event.data);
      // Ги чуваме само последните 5 сигнали за да не се преполни екранот
      setSignals((prev) => [newSignal, ...prev].slice(0, 5));
    };

    ws.onerror = () => setStatus("Backend Offline - Ве молам стартувајте го main.py");
    ws.onclose = () => setStatus("Disconnected from AI Engine");

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-[#050505] text-white p-6 md:p-12 font-sans">
      {/* Header */}
      <div className="flex justify-between items-end mb-10 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-6xl font-black text-yellow-500 tracking-tighter">
            LCDK <span className="text-white">TRADING</span>
          </h1>
          <p className="text-zinc-500 font-mono mt-2 uppercase tracking-widest text-sm">
            VIP Artificial Intelligence Terminal v1.0
          </p>
        </div>
        <div className="text-right">
          <div className={`flex items-center gap-2 justify-end font-bold ${status.includes('LIVE') ? 'text-green-500' : 'text-red-500'}`}>
            <span className={`w-3 h-3 rounded-full ${status.includes('LIVE') ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
            {status}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Главна секција за сигнали */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-zinc-400 mb-4">REAL-TIME AI PICKS</h2>
          {signals.length === 0 && (
            <div className="p-20 text-center border-2 border-dashed border-zinc-800 rounded-3xl text-zinc-600">
              Waiting for AI market analysis...
            </div>
          )}
          {signals.map((s, i) => (
            <div 
              key={i} 
              className={`group relative overflow-hidden p-6 rounded-3xl border transition-all duration-500 ${
                s.signal === 'BUY' 
                ? 'bg-green-500/5 border-green-500/20 hover:border-green-500/50' 
                : 'bg-red-500/5 border-red-500/20 hover:border-red-500/50'
              }`}
            >
              <div className="flex justify-between items-center relative z-10">
                <div>
                  <h3 className="text-4xl font-black tracking-tight">{s.ticker}</h3>
                  <p className="text-zinc-500 font-mono text-lg">${s.price}</p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-black mb-1 ${s.signal === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                    {s.signal}
                  </div>
                  <div className="bg-zinc-800 rounded-full px-3 py-1 text-xs font-bold text-zinc-300">
                    AI CONFIDENCE: {Math.round(s.confidence * 100)}%
                  </div>
                </div>
              </div>
              {/* Декоративна линија во позадина */}
              <div className={`absolute bottom-0 left-0 h-1 transition-all duration-1000 ${s.signal === 'BUY' ? 'bg-green-500' : 'bg-red-500'}`} style={{ width: `${s.confidence * 100}%` }}></div>
            </div>
          ))}
        </div>

        {/* Десна секција за Портфолио */}
        <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-[2rem]">
          <h2 className="text-xl font-bold mb-6 italic text-yellow-500 underline decoration-zinc-700">PORTFOLIO OPTIMIZER</h2>
          <div className="space-y-6">
             <div className="p-4 bg-black/40 rounded-2xl border border-zinc-800">
                <p className="text-xs text-zinc-500 mb-1">STRATEGY</p>
                <p className="font-bold">Max Sharpe Ratio</p>
             </div>
             <div className="p-4 bg-black/40 rounded-2xl border border-zinc-800">
                <p className="text-xs text-zinc-500 mb-1">RISK LEVEL</p>
                <p className="font-bold text-yellow-500">DYNAMIC (AI CONTROLLED)</p>
             </div>
             <div className="mt-10 pt-10 border-t border-zinc-800 text-center">
                <div className="inline-block p-4 rounded-full bg-yellow-500/10 mb-4">
                   <div className="w-8 h-8 border-4 border-yellow-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <p className="text-sm text-zinc-400">AI is re-balancing your VIP portfolio based on new volatility data...</p>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}