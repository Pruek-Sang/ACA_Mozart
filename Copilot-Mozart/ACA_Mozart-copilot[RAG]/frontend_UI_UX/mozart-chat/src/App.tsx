import { useState } from 'react';
import { Header } from './components/Header';
import { ChatPane } from './components/ChatPane';
import { InputBar } from './components/InputBar';
import { ApiKeyModal } from './components/ApiKeyModal';
import { JSONEditorPane } from './components/JSONEditorPane';
import { useChat } from './hooks/useChat';

function App() {
  const {
    messages,
    isTyping,
    isAuthenticated,
    apiKey,
    jsonData,
    setApiKey,
    send,
    clearMessages,
  } = useChat();

  const [showSettings, setShowSettings] = useState(false);

  const handleQuickSelect = (text: string) => {
    send(text);
  };

  const handleSendToMcp = (data: Record<string, unknown>) => {
    console.log('Sending to MCP:', data);
    send(`คำนวณจาก JSON: ${JSON.stringify(data).slice(0, 100)}...`);
  };

  // ===== LOGIN SCREEN (Block access until authenticated) =====
  if (!isAuthenticated) {
    return (
      <div className="h-screen bg-black flex items-center justify-center relative overflow-hidden">
        {/* Aurora Background */}
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

        {/* Login Modal */}
        <ApiKeyModal
          visible={true}
          onSave={(key) => setApiKey(key)}
          initialKey=""
        />
      </div>
    );
  }

  // ===== MAIN APP (After authenticated) =====
  return (
    <div className="h-screen bg-black text-textPrimary flex items-center justify-center p-6 relative overflow-hidden">
      {/* Logo Watermark Placeholder */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
        <div className="text-[200px] font-bold text-white/5 select-none tracking-widest">
          ACA
        </div>
      </div>

      {/* Aurora Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute w-[600px] h-[600px] rounded-full opacity-15 blur-3xl"
          style={{
            background: 'radial-gradient(circle, #6366F1 0%, transparent 70%)',
            top: '10%',
            left: '5%',
          }}
        />
        <div
          className="absolute w-[600px] h-[600px] rounded-full opacity-15 blur-3xl"
          style={{
            background: 'radial-gradient(circle, #A855F7 0%, transparent 70%)',
            bottom: '10%',
            right: '5%',
          }}
        />
      </div>

      {/* ===== DUAL PHONE CONTAINER ===== */}
      <div className="relative z-10 flex gap-6 w-full h-full max-w-[1600px]">

        {/* ===== LEFT PHONE: Chat ===== */}
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

        {/* ===== RIGHT PHONE: JSON Editor ===== */}
        <div className="phone-frame flex-1">
          <JSONEditorPane data={jsonData} onSendToMcp={handleSendToMcp} />
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
