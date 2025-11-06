import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Templates 공통 스타일 (한국도로공사 디자인 시스템)
import './styles/templates/font.css'
import './styles/templates/common.css'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
