import { Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Navbar from './components/layout/Navbar'
import ToastContainer from './components/shared/Toast'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Brand from './pages/Brand'
import Debate from './pages/Debate'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'
import { useSettingsStore } from './store/settingsStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <main className="pt-14 lg:pt-16 transition-all duration-300">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/debate" element={<Debate />} />
            <Route path="/brand" element={<Brand />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <ToastContainer />
      </div>
    </QueryClientProvider>
  )
}

export default App
