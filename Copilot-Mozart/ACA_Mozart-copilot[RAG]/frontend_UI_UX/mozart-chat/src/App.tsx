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
    setJsonData,
  } = useChat();

  const [showSettings, setShowSettings] = useState(false);

  const handleQuickSelect = (text: string) => {
    send(text);
  };

  const handleSendToMcp = (data: Record<string, unknown>) => {
    // TODO: Implement MCP calculation call
    console.log('Sending to MCP:', data);
    send(`คำนวณจาก JSON: ${JSON.stringify(data).slice(0, 100)}...`);
  };

  return (
    <div className="h-screen bg-bgPrimary text-textPrimary flex relative overflow-hidden">
      {/* Aurora Background */}
      <div className="absolute inset-0 pointer-events-none z-0">
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

      {/* Content */}
      <div className="relative z-10 flex w-full">
        {/* Left Pane - Chat (40%) */}
        <div className="w-2/5 flex flex-col border-r border-gray-800">
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

        {/* Right Pane - JSON Editor (60%) */}
        <div className="w-3/5 bg-bgPrimary">
          <JSONEditorPane data={jsonData} onSendToMcp={handleSendToMcp} />
        </div>
      </div>

      {/* API Key Modal */}
      <ApiKeyModal
        visible={!isAuthenticated || showSettings}
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
