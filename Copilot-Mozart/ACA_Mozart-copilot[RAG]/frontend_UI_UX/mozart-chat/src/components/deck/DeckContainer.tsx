import React, { Children, cloneElement, isValidElement } from 'react';
import type { ReactElement, CSSProperties, ReactNode } from 'react';

interface DeckContainerProps {
    children: ReactNode;
}

export const DeckContainer: React.FC<DeckContainerProps> = ({ children }) => {
    const arrayChildren = Children.toArray(children);
    const totalCards = arrayChildren.length;
    // Calculate middle index to center the fan
    const middleIndex = Math.floor(totalCards / 2);

    return (
        <div className="relative w-full h-screen flex items-center justify-center bg-gray-900 overflow-hidden">
            {/* Ambient Background Aura */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#1a103c] via-[#2d1b4e] to-[#0f0a28] pointer-events-none" />
            <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_50%_50%,rgba(147,51,234,0.3),transparent_70%)] pointer-events-none" />

            <div
                className="group relative flex items-center justify-center h-[600px] w-full max-w-6xl mx-auto perspective-[1000px]"
            >
                {Children.map(arrayChildren, (child, index) => {
                    if (!isValidElement(child)) return child;

                    // Calculate rotation value: centered around 0
                    // e.g. for 5 cards: -2, -1, 0, 1, 2
                    const rotateVal = (index - middleIndex) * 5;

                    return cloneElement(child as ReactElement<any>, {
                        style: {
                            '--r': rotateVal,
                        } as CSSProperties,
                        // Pass index for potential staggered animations if needed
                        index,
                    });
                })}
            </div>
        </div>
    );
};
