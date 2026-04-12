import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Debate from './pages/Debate'
import Brand from './pages/Brand'

function App() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="pt-16">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/debate" element={<Debate />} />
          <Route path="/brand" element={<Brand />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
