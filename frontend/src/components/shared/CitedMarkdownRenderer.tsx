/**
 * CitedMarkdownRenderer — renders markdown with clickable [N] citation links.
 *
 * Enhanced features:
 * - Clickable citation badges that open source URLs
 * - Key insight boxes (blockquotes styled as callouts)
 * - Visual hierarchy with better headings, bold text, and lists
 * - Summary extraction for TL;DR sections
 * - Human-readable formatting with proper spacing
 *
 * Props:
 *   content    — the markdown string (may contain [1], [2] etc.)
 *   urlMap     — { '1': 'https://...', '2': '...' } from backend citations_map event
 *   accentColor — hex color for citation badges (defaults to blue)
 *   className?: string
 */
import { useMemo } from 'react'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

interface CitedMarkdownRendererProps {
  content: string
  urlMap?: Record<string, string>
  accentColor?: string
  className?: string
}

/**
 * Pre-process markdown: replace [N] citation markers with inline HTML anchor badges.
 * Skips markdown link syntax like [text](url).
 */
function substituteCitations(
  content: string,
  urlMap: Record<string, string>,
  accentColor: string
): string {
  if (!urlMap || Object.keys(urlMap).length === 0) return content

  return content.replace(/\[(\d+(?:,\s*\d+)*)\](?!\()/g, (_match, inner) => {
    const nums = inner.split(/[,\s]+/).filter(Boolean)
    return nums
      .map((num: string) => {
        const n = num.trim()
        const url = urlMap[n]
        if (url && url.startsWith('http')) {
          return (
            `<a href="${url}" target="_blank" rel="noopener noreferrer" ` +
            `class="citation-badge" ` +
            `style="display:inline-flex;align-items:center;justify-content:center;` +
            `min-width:20px;height:20px;border-radius:50%;` +
            `background:${accentColor};color:#fff;font-size:10px;font-weight:900;` +
            `text-decoration:none;vertical-align:super;margin:0 2px;line-height:1;` +
            `cursor:pointer;box-shadow:0 2px 6px ${accentColor}40;` +
            `padding:0 4px;transition:all 0.2s cubic-bezier(0.34,1.56,0.64,1);` +
            `border:2px solid ${accentColor}60;" ` +
            `onmouseover="this.style.transform='scale(1.3)';this.style.boxShadow='0 4px 12px ${accentColor}60';this.style.background='${accentColor}dd'" ` +
            `onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 2px 6px ${accentColor}40';this.style.background='${accentColor}'" ` +
            `title="Source [${n}]: ${url}">[${n}]</a>`
          )
        } else {
          return (
            `<sup style="display:inline-flex;align-items:center;justify-content:center;` +
            `min-width:18px;height:18px;border-radius:50%;background:#e5e7eb;` +
            `color:#4b5563;font-size:9px;font-weight:700;vertical-align:super;` +
            `margin:0 1px;padding:0 3px;border:1px solid #d1d5db;">[${n}]</sup>`
          )
        }
      })
      .join('')
  })
}

/**
 * Enhance blockquotes as styled callout/insight boxes
 */
function enhanceBlockquotes(html: string, accentColor: string): string {
  return html.replace(
    /<blockquote>([\s\S]*?)<\/blockquote>/g,
    (_match, content) => {
      return (
        `<div class="insight-callout" style="` +
        `background:linear-gradient(135deg, ${accentColor}08 0%, ${accentColor}03 100%);` +
        `border-left:4px solid ${accentColor};` +
        `border-radius:0 12px 12px 0;` +
        `padding:16px 20px;` +
        `margin:16px 0;` +
        `box-shadow:0 2px 8px ${accentColor}10;">` +
        `<div style="display:flex;align-items:flex-start;gap:10px;">` +
        `<span style="font-size:18px;line-height:1;">💡</span>` +
        `<div style="flex:1;min-width:0;">${content}</div>` +
        `</div></div>`
      )
    }
  )
}

/**
 * Enhance bold text with accent color highlights
 */
function enhanceBoldText(html: string, accentColor: string): string {
  return html.replace(
    /<strong>([\s\S]*?)<\/strong>/g,
    (_match, content) => {
      return `<strong style="color:${accentColor};font-weight:800;">${content}</strong>`
    }
  )
}

/**
 * Enhance headings with accent underlines
 */
function enhanceHeadings(html: string, accentColor: string): string {
  return html
    .replace(
      /<h3>([\s\S]*?)<\/h3>/g,
      (_match, content) =>
        `<h3 style="border-bottom:2px solid ${accentColor}30;padding-bottom:8px;margin-top:24px;margin-bottom:12px;">${content}</h3>`
    )
    .replace(
      /<h4>([\s\S]*?)<\/h4>/g,
      (_match, content) =>
        `<h4 style="color:${accentColor};margin-top:20px;margin-bottom:8px;">${content}</h4>`
    )
}

/**
 * Enhance list items with better visual markers
 */
function enhanceLists(html: string, accentColor: string): string {
  return html
    .replace(
      /<ul>/g,
      `<ul style="list-style:none;padding-left:0;">`
    )
    .replace(
      /<li>/g,
      `<li style="position:relative;padding-left:20px;margin-bottom:8px;"><span style="position:absolute;left:0;top:2px;width:8px;height:8px;border-radius:50%;background:${accentColor}40;display:inline-block;"></span>`
    )
}

export default function CitedMarkdownRenderer({
  content,
  urlMap = {},
  accentColor = '#3b82f6',
  className = '',
}: CitedMarkdownRendererProps) {
  const html = useMemo(() => {
    try {
      const withCitations = substituteCitations(content, urlMap, accentColor)
      let parsed = marked.parse(withCitations) as string
      parsed = enhanceBlockquotes(parsed, accentColor)
      parsed = enhanceBoldText(parsed, accentColor)
      parsed = enhanceHeadings(parsed, accentColor)
      parsed = enhanceLists(parsed, accentColor)
      return parsed
    } catch {
      return content
    }
  }, [content, urlMap, accentColor])

  return (
    <div
      className={`prose prose-sm max-w-none prose-gray ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
