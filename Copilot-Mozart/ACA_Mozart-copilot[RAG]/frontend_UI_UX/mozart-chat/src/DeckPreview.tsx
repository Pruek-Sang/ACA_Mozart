import React, { useState } from 'react';
import { DeckContainer } from './components/deck/DeckContainer';
import { MagicalCard } from './components/deck/MagicalCard';
import { MousePointer2, Zap, FileText, Component, LayoutTemplate } from 'lucide-react';

export const DeckPreview = () => {
    // This component is for DEVELOPMENT & VISUAL VERIFICATION only.
    // It allows testing the Deck UI in isolation without the main app context.

    return (
        <div className="w-full h-screen bg-black overflow-hidden relative">
            {/* 
                DEBUG NOTE: 
                The user reported "White background covers everything".
                This might be because the global app background was fighting with DeckContainer.
                Here we enforce a dark context.
            */}

            <DeckContainer>
                {/* 1. Chat Card */}
                <MagicalCard
                    title="Magic Chat"
                    icon={<MousePointer2 className="w-5 h-5 text-amber-200" />}
                    className="w-[450px] h-[700px]"
                >
                    <div className="flex flex-col h-full items-center justify-center text-center p-8 space-y-4">
                        <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center">
                            <span className="text-3xl">✨</span>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-800">Chat Interface</h2>
                        <p className="text-gray-500">
                            This is the main interaction area.
                            The white background here is intended for readability.
                            Does it cover the gold border?
                        </p>
                    </div>
                </MagicalCard>

                {/* 2. Load Schedule */}
                <MagicalCard
                    title="Load Schedule"
                    icon={<Zap className="w-5 h-5 text-amber-200" />}
                    className="w-[450px] h-[700px]"
                >
                    <div className="flex flex-col items-center justify-center h-full text-center p-6 text-gray-400">
                        <Zap className="w-16 h-16 mb-4 text-amber-500" />
                        <h3 className="text-xl font-bold text-gray-600 mb-2">Load Schedule</h3>
                        <p>Circuit Analysis Module</p>
                    </div>
                </MagicalCard>

                {/* 3. SLD */}
                <MagicalCard
                    title="Single Line Diagram"
                    icon={<Component className="w-5 h-5 text-amber-200" />}
                    className="w-[450px] h-[700px]"
                >
                    <div className="flex flex-col items-center justify-center h-full text-center p-6 text-gray-400">
                        <Component className="w-16 h-16 mb-4 text-amber-500" />
                        <h3 className="text-xl font-bold text-gray-600 mb-2">SLD Viewer</h3>
                        <p>Schematic Generation</p>
                    </div>
                </MagicalCard>

                {/* 4. BOQ */}
                <MagicalCard
                    title="Bill of Quantities"
                    icon={<FileText className="w-5 h-5 text-amber-200" />}
                    className="w-[450px] h-[700px]"
                >
                    <div className="flex flex-col items-center justify-center h-full text-center p-6 text-gray-400">
                        <FileText className="w-16 h-16 mb-4 text-amber-500" />
                        <h3 className="text-xl font-bold text-gray-600 mb-2">Cost Estimate</h3>
                        <p>Pricing & Inventory</p>
                    </div>
                </MagicalCard>

                {/* 5. Floor Plan */}
                <MagicalCard
                    title="Floor Plan"
                    icon={<LayoutTemplate className="w-5 h-5 text-amber-200" />}
                    className="w-[800px] h-[600px]"
                >
                    <div className="w-full h-full bg-gray-100 flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg">
                        <span className="text-gray-400">Floor Plan Visualization Area</span>
                    </div>
                </MagicalCard>
            </DeckContainer>
        </div>
    );
};
