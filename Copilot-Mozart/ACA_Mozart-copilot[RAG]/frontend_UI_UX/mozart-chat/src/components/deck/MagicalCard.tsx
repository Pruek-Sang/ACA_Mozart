import React from 'react';

interface MagicalCardProps {
    title: string;
    icon?: React.ReactNode;
    children?: React.ReactNode;
    isActive?: boolean;
    style?: React.CSSProperties;
    className?: string;
}

export const MagicalCard: React.FC<MagicalCardProps> = ({
    title,
    icon,
    children,
    style,
    className = ''
}) => {
    return (
        <div
            className={`
        relative 
        w-[280px] h-[400px] 
        transition-all duration-500 ease-out
        transform 
        rotate-[calc(var(--r)*1deg)]
        group-hover:rotate-0
        group-hover:mx-4
        -mx-12
        flex flex-col
        rounded-xl
        shadow-2xl
        select-none
        ${className}
      `}
            style={style}
        >
            {/* 
        --------------------------
        THE MAGICAL-INDUSTRIAL FRAME 
        --------------------------
      */}

            {/* 1. Base Obsidian Slate (Background) */}
            <div className="absolute inset-0 bg-gradient-to-b from-gray-900 to-black rounded-xl border border-gray-800" />

            {/* 2. Gold Circuitry Edge Glow (Pseudo-border) */}
            <div className="absolute -inset-[2px] rounded-xl bg-gradient-to-b from-amber-300 via-yellow-500 to-amber-700 opacity-80 blur-[1px] -z-10" />

            {/* 3. Mechanical Engravings / Metallic Rim (The 'Frame') */}
            <div className="absolute inset-0 rounded-xl border-[3px] border-amber-600/50 shadow-[inset_0_0_20px_rgba(0,0,0,0.8)] z-10 pointer-events-none">
                {/* Corner Decors (Top-Left) */}
                <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-amber-400 rounded-tl-md" />
                {/* Corner Decors (Top-Right) */}
                <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-amber-400 rounded-tr-md" />
                {/* Corner Decors (Bottom-Left) */}
                <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-amber-400 rounded-bl-md" />
                {/* Corner Decors (Bottom-Right) */}
                <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-amber-400 rounded-br-md" />
            </div>

            {/* 
        --------------------------
        CARD CONTENT 
        --------------------------
      */}

            {/* Header (Gold/Amber Tab) */}
            <div className="relative h-14 bg-gradient-to-r from-amber-700 via-amber-600 to-amber-800 rounded-t-xl flex items-center justify-between px-4 border-b-2 border-amber-400/30 z-20">
                <span className="text-amber-100 font-bold tracking-wider uppercase text-sm drop-shadow-md flex items-center gap-2">
                    {icon && <span className="text-amber-200">{icon}</span>}
                    {title}
                </span>
                <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-amber-300 shadow-[0_0_5px_#fcd34d]" />
                    <div className="w-2 h-2 rounded-full bg-amber-900/50" />
                </div>
            </div>

            {/* Body (Dark Obsidian Content Area) */}
            <div className="relative flex-1 bg-gray-900/90 m-4 mt-0 rounded-b-[10px] overflow-hidden group-hover:overflow-y-auto z-20 shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)] border border-t-0 border-amber-500/20 backdrop-blur-sm">
                <div className="p-4 text-gray-100 text-sm font-light tracking-wide">
                    {children}
                </div>

                {/* Inner Shadow for depth */}
                <div className="absolute inset-0 pointer-events-none shadow-[inset_0_5px_10px_rgba(0,0,0,0.1)]" />
            </div>

            {/* 
        --------------------------
        MAGICAL HOVER EFFECTS 
        --------------------------
      */}
            {/* Reflection Glare */}
            <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/10 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none z-30 rounded-xl" />

        </div>
    );
};
