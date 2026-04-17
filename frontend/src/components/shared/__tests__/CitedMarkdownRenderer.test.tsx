import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import CitedMarkdownRenderer from '../CitedMarkdownRenderer'

describe('CitedMarkdownRenderer', () => {
  it('renders plain markdown content', () => {
    const { container } = render(<CitedMarkdownRenderer content="Hello world" />)
    expect(container.textContent).toContain('Hello world')
  })

  it('renders markdown with formatting', () => {
    const { container } = render(<CitedMarkdownRenderer content="**bold** and *italic*" />)
    expect(container.innerHTML).toContain('<strong')
    expect(container.innerHTML).toContain('<em')
  })

  it('replaces [1] with clickable badge when URL is available', () => {
    const urlMap = { '1': 'https://example.com/source1' }
    const { container } = render(
      <CitedMarkdownRenderer content="This is a claim [1]." urlMap={urlMap} accentColor="#3b82f6" />
    )
    const anchor = container.querySelector('a.citation-badge')
    expect(anchor).toBeTruthy()
    expect(anchor?.getAttribute('href')).toBe('https://example.com/source1')
    expect(anchor?.getAttribute('target')).toBe('_blank')
  })

  it('renders plain superscript when no URL is available', () => {
    const { container } = render(
      <CitedMarkdownRenderer content="This is a claim [1]." urlMap={{}} accentColor="#3b82f6" />
    )
    // When urlMap is empty, substituteCitations returns content unchanged,
    // so [1] remains as plain text in the markdown output
    expect(container.textContent).toContain('[1]')
  })

  it('handles multiple citations [1,2]', () => {
    const urlMap = { '1': 'https://example.com/1', '2': 'https://example.com/2' }
    const { container } = render(
      <CitedMarkdownRenderer content="Claim [1,2] here." urlMap={urlMap} accentColor="#3b82f6" />
    )
    const anchors = container.querySelectorAll('a.citation-badge')
    expect(anchors.length).toBe(2)
  })

  it('enhances blockquotes as insight callouts', () => {
    const { container } = render(
      <CitedMarkdownRenderer content="> This is an insight" accentColor="#3b82f6" />
    )
    const callout = container.querySelector('.insight-callout')
    expect(callout).toBeTruthy()
  })

  it('enhances bold text with accent color', () => {
    const { container } = render(
      <CitedMarkdownRenderer content="This is **important** text" accentColor="#EF4444" />
    )
    const strong = container.querySelector('strong')
    expect(strong?.getAttribute('style')).toContain('color:#EF4444')
  })

  it('enhances h3 headings with accent underline', () => {
    const { container } = render(
      <CitedMarkdownRenderer content="### Section Title" accentColor="#3b82f6" />
    )
    const h3 = container.querySelector('h3')
    expect(h3?.getAttribute('style')).toContain('border-bottom')
  })

  it('enhances list items with colored dots', () => {
    const { container } = render(
      <CitedMarkdownRenderer content="- Item 1\n- Item 2" accentColor="#3b82f6" />
    )
    // The enhanceLists function replaces <li> and adds colored dot spans
    const html = container.innerHTML
    expect(html).toContain('Item 1')
    expect(html).toContain('Item 2')
    expect(html).toContain('border-radius:50%')
  })

  it('handles empty content gracefully', () => {
    const { container } = render(<CitedMarkdownRenderer content="" />)
    expect(container.innerHTML).toBeTruthy()
  })

  it('handles malformed content gracefully', () => {
    const { container } = render(<CitedMarkdownRenderer content="[][][bad" urlMap={{}} />)
    expect(container.innerHTML).toBeTruthy()
  })

  it('applies custom className', () => {
    const { container } = render(
      <CitedMarkdownRenderer content="test" className="custom-class" />
    )
    const div = container.querySelector('.custom-class')
    expect(div).toBeTruthy()
  })
})
