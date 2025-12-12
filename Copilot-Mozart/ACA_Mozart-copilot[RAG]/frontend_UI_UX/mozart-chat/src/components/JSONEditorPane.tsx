import { Code, Rocket } from 'lucide-react';
import { useState, useEffect } from 'react';

interface JSONEditorPaneProps {
    data: Record<string, unknown> | null;
    onSendToMcp?: (data: Record<string, unknown>) => void;
}

export function JSONEditorPane({ data, onSendToMcp }: JSONEditorPaneProps) {
    const [jsonText, setJsonText] = useState('');
    const [isValid, setIsValid] = useState(true);

    useEffect(() => {
        if (data) {
            setJsonText(JSON.stringify(data, null, 2));
            setIsValid(true);
        }
    }, [data]);

    const handleChange = (value: string) => {
        setJsonText(value);
        try {
            JSON.parse(value);
            setIsValid(true);
        } catch {
            setIsValid(false);
        }
    };

    const handleSend = () => {
        if (!isValid || !onSendToMcp) return;
        try {
            const parsed = JSON.parse(jsonText);
            onSendToMcp(parsed);
        } catch {
            // Handle error
        }
    };

    if (!data) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-gray-600 p-8">
                <Code className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-lg font-medium mb-2">JSON Workspace</p>
                <p className="text-sm text-center max-w-xs">
                    เมื่อระบบสร้าง Spec หรือ JSON Data จะแสดงที่นี่
                    <br />
                    คุณสามารถแก้ไขและส่งไปคำนวณได้
                </p>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-bgSecondary/50">
                <div className="flex items-center gap-2">
                    <Code className="w-5 h-5 text-accentMozart" />
                    <span className="font-medium">JSON Editor</span>
                    {!isValid && (
                        <span className="text-xs text-red-400 ml-2">⚠️ Invalid JSON</span>
                    )}
                </div>
                <button
                    onClick={handleSend}
                    disabled={!isValid}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-accentMozart to-accentAmadeus text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-all"
                >
                    <Rocket className="w-4 h-4" />
                    <span>Send to MCP</span>
                </button>
            </div>

            {/* Editor */}
            <div className="flex-1 p-4 overflow-auto">
                <textarea
                    value={jsonText}
                    onChange={(e) => handleChange(e.target.value)}
                    className={`w-full h-full bg-black/50 text-green-400 font-mono text-sm p-4 rounded-lg border resize-none focus:outline-none focus:ring-2 ${isValid
                            ? 'border-gray-700 focus:ring-accentMozart'
                            : 'border-red-500 focus:ring-red-500'
                        }`}
                    spellCheck={false}
                />
            </div>
        </div>
    );
}
