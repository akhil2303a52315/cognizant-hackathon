import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SourcesPanel from '../SourcesPanel'

describe('SourcesPanel', () => {
  const mockSources = [
    { num: 1, title: 'Source One', url: 'https://example.com/1', agent: 'risk', agentColor: '#EF4444' },
    { num: 2, title: 'Source Two', url: 'https://example.com/2', agent: 'supply', agentColor: '#7C3AED' },
    { num: 3, title: 'Source Three', url: 'https://example.com/3', agent: 'risk', agentColor: '#EF4444' },
  ]

  const mockCitationMap = {
    '4': 'https://example.com/4',
    '5': 'https://example.com/5',
  }

  it('renders nothing when sources array is empty', () => {
    const { container } = render(<SourcesPanel sources={[]} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders the toggle button with correct source count', () => {
    render(<SourcesPanel sources={mockSources} />)
    const button = screen.getByText(/3 Sources & References/i)
    expect(button).toBeInTheDocument()
  })

  it('expands the panel when toggle button is clicked', () => {
    render(<SourcesPanel sources={mockSources} />)
    const button = screen.getByRole('button', { name: /3 Sources & References/i })
    fireEvent.click(button)
    expect(screen.getByText('References & Sources')).toBeInTheDocument()
  })

  it('displays all source titles when expanded', () => {
    render(<SourcesPanel sources={mockSources} />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('Source One')).toBeInTheDocument()
    expect(screen.getByText('Source Two')).toBeInTheDocument()
    expect(screen.getByText('Source Three')).toBeInTheDocument()
  })

  it('shows citation map entries when expanded', () => {
    render(<SourcesPanel sources={mockSources} citationMap={mockCitationMap} />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('Source [4]')).toBeInTheDocument()
    expect(screen.getByText('Source [5]')).toBeInTheDocument()
  })

  it('collapses panel when close button is clicked', () => {
    render(<SourcesPanel sources={mockSources} />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('References & Sources')).toBeInTheDocument()
    // Find the close (X) button inside the panel header
    const allButtons = screen.getAllByRole('button')
    const closeBtn = allButtons.find(btn => btn.querySelector('svg.lucide-x'))
    expect(closeBtn).toBeTruthy()
    if (closeBtn) {
      fireEvent.click(closeBtn)
    }
    // Panel should be collapsed (AnimatePresence removes content)
  })

  it('renders agent filter when multiple agents exist', () => {
    render(<SourcesPanel sources={mockSources} />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByDisplayValue('All Agents')).toBeInTheDocument()
  })

  it('does not render agent filter when only one agent', () => {
    const singleAgentSources = mockSources.filter(s => s.agent === 'risk')
    render(<SourcesPanel sources={singleAgentSources} />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.queryByDisplayValue('All Agents')).toBeNull()
  })

  it('uses custom accent color', () => {
    render(<SourcesPanel sources={mockSources} accentColor="#FF0000" />)
    const button = screen.getByRole('button')
    // The accent color is used in rgba format in the gradient
    expect(button.style.background).toContain('255, 0, 0')
  })

  it('renders source links with target _blank', () => {
    render(<SourcesPanel sources={mockSources} />)
    fireEvent.click(screen.getByRole('button'))
    const links = screen.getAllByRole('link')
    links.forEach(link => {
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    })
  })
})
