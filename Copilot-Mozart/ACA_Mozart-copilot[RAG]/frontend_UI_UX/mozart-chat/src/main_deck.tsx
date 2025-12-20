import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { DeckPreview } from './DeckPreview'

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <DeckPreview />
    </StrictMode>,
)
