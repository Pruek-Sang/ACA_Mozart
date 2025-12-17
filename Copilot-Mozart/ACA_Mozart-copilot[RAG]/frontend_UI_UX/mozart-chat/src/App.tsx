
// src/App.tsx
// Version 2: Replaced JSON Editor with Floor Plan Visualizer

import { useState } from 'react';
import { Header } from './components/Header';
import { ChatPane } from './components/ChatPane';
import { InputBar } from './components/InputBar';
import { ApiKeyModal } from './components/ApiKeyModal';
import { useChat } from './hooks/useChat';
import FloorPlanVisualizer from './features/floorplan/FloorPlanVisualizer'; // 🆕 Import the new component

function App() {
  const {
    // Chat-related state
    messages,
    isTyping,
    send,
    clearMessages,
    // Auth-related state
    isAuthenticated,
    apiKey,
    setApiKey,
    // **[NEW]** Floor plan data
    rooms,
  } = useChat();

  const [showSettings, setShowSettings] = useState(false);

  const handleQuickSelect = (text: string) => {
    send(text);
  };

  // ===== LOGIN SCREEN =====
  if (!isAuthenticated) {
    return (
      <div className="h-screen bg-black flex items-center justify-center relative overflow-hidden">
        {/* Background effects... */}
        <div className="absolute inset-0 pointer-events-none">
          <div
            className="absolute w-[500px] h-[500px] rounded-full opacity-20 blur-3xl"
            style={{
              background: 'radial-gradient(circle, #6366F1 0%, transparent 70%)',
              top: '20%',
              left: '10%',
            }}
          />
          <div
            className="absolute w-[500px] h-[500px] rounded-full opacity-20 blur-3xl"
            style={{
              background: 'radial-gradient(circle, #A855F7 0%, transparent 70%)',
              bottom: '10%',
              right: '10%',
            }}
          />
        </div>
        <ApiKeyModal
          visible={true}
          onSave={(key) => setApiKey(key)}
          initialKey=""
        />
      </div>
    );
  }

  // ===== MAIN APP =====
  return (
    <div className="h-screen bg-black text-textPrimary flex items-center justify-center p-6 relative overflow-hidden">

      {/* Aurora Background (Whitish-Purple) - Enhanced for Visibility */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div
          className="absolute w-[1000px] h-[1000px] rounded-full opacity-60 blur-[120px] animate-pulse"
          style={{
            background: 'radial-gradient(circle, #4F46E5 0%, transparent 60%)', // Indigo-600
            top: '-20%',
            left: '-20%',
            animationDuration: '10s'
          }}
        />
        <div
          className="absolute w-[800px] h-[800px] rounded-full opacity-60 blur-[120px] animate-pulse"
          style={{
            background: 'radial-gradient(circle, #9333EA 0%, transparent 60%)', // Purple-600
            bottom: '-10%',
            right: '-10%',
            animationDuration: '15s'
          }}
        />
        {/* Floating stars/particles layer */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-150 contrast-150 mix-blend-overlay"></div>
      </div>

      {/* Logo Watermark Placeholder (Faded) */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
        <div className="text-[200px] font-bold text-gray-900/5 select-none tracking-widest">
          ACA
        </div>
      </div>

      {/* ===== DUAL PANE CONTAINER ===== */}
      <div className="relative z-10 flex gap-6 w-full h-full max-w-[1600px]">

        {/* ===== LEFT PANE: Chat ===== */}
        <div className="phone-frame flex-1 flex flex-col">
          <Header
            onClear={clearMessages}
            onSettings={() => setShowSettings(true)}
          />
          <ChatPane
            messages={messages}
            isTyping={isTyping}
            onQuickSelect={handleQuickSelect}
          />
          <InputBar onSend={send} disabled={isTyping} />
        </div>

        {/* ===== RIGHT PANE: Floor Plan Visualizer 🆕 ===== */}
        <div className="phone-frame flex-1 flex flex-col overflow-hidden">
          <FloorPlanVisualizer
            rooms={rooms}
            chatText={messages.filter(m => m.role === 'bot').slice(-1)[0]?.content || ''}
          />
        </div>

      </div>

      {/* Settings Modal */}
      <ApiKeyModal
        visible={showSettings}
        onSave={(key) => {
          setApiKey(key);
          setShowSettings(false);
        }}
        initialKey={apiKey}
      />
    </div>
  );
}

export default App;
