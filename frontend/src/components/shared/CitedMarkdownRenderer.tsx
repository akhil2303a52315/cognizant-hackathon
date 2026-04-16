/**
 * CitedMarkdownRenderer — renders markdown with clickable [N] citation links.
 *
 * Replaces [N] and [N,M] inline citation markers with circular anchor badges
 * that open the source URL in a new tab on click.
 *
 * Props:
 *   content    — the markdown string (may contain [1], [2] etc.)
 *   urlMap     — { '1': 'https://...', '2': '...' } from backend citations_map event
 *   accentColor — hex color for citation badges (defaults to blue)
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
          // Clickable badge — opens URL in new tab
          return (
            `<a href="${url}" target="_blank" rel="noopener noreferrer" ` +
            `style="display:inline-flex;align-items:center;justify-content:center;` +
            `min-width:19px;height:19px;border-radius:50%;` +
            `background:${accentColor};color:#fff;font-size:10px;font-weight:900;` +
            `text-decoration:none;vertical-align:super;margin:0 1px;line-height:1;` +
            `cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.25);` +
            `padding:0 3px;transition:all 0.15s ease;" ` +
            `onmouseover="this.style.transform='scale(1.25)';this.style.boxShadow='0 3px 8px rgba(0,0,0,0.35)'" ` +
            `onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 1px 3px rgba(0,0,0,0.25)'" ` +
            `title="Source [${n}]: ${url}">[${n}]</a>`
          )
        } else {
          // No URL available — render as plain superscript
          return (
            `<sup style="display:inline-flex;align-items:center;justify-content:center;` +
            `min-width:17px;height:17px;border-radius:50%;background:#e5e7eb;` +
            `color:#4b5563;font-size:9px;font-weight:700;vertical-align:super;` +
            `margin:0 1px;padding:0 3px;">[${n}]</sup>`
          )
        }
      })
      .join('')
  })
}

export default function CitedMarkdownRenderer({
  content,
  urlMap = {},
  accentColor = '#3b82f6',
  className = '',
}: CitedMarkdownRendererProps) {
  const html = useMemo(() => {
    try {
      // First substitute [N] with anchor badges, then parse markdown
      const withCitations = substituteCitations(content, urlMap, accentColor)
      return marked.parse(withCitations) as string
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
