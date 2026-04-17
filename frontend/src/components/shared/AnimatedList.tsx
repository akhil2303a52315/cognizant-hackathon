import { useRef, useEffect } from 'react';

interface SourceItem {
  num: number;
  title: string;
  url: string;
  agent: string;
  agentColor: string;
}

interface AnimatedListProps {
  items: SourceItem[];
  className?: string;
  maxHeight?: string;
}

const AnimatedList = ({
  items = [],
  className = '',
  maxHeight = '200px'
}: AnimatedListProps) => {
  const listRef = useRef<HTMLDivElement>(null);
  const prevItemsLengthRef = useRef(0);

  // Auto-scroll to bottom when new items are added
  useEffect(() => {
    if (listRef.current && items.length > prevItemsLengthRef.current) {
      const container = listRef.current;
      // Use setTimeout to ensure DOM has updated
      setTimeout(() => {
        container.scrollTop = container.scrollHeight;
      }, 50);
    }
    prevItemsLengthRef.current = items.length;
  }, [items.length]);

  if (items.length === 0) {
    return (
      <div className={`text-white/30 text-xs ${className}`}>
        Waiting for sources...
      </div>
    );
  }

  return (
    <div 
      ref={listRef}
      className={`overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent ${className}`}
      style={{ maxHeight }}
    >
      {items.map((item, index) => (
        <a
          key={`${item.agent}-${item.num}-${index}`}
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-200 group mb-1"
          style={{ borderLeftColor: item.agentColor, borderLeftWidth: '3px' }}
        >
          <span className="text-white/40 font-mono">[{item.num}]</span>
          <span className="text-white/80 flex-1 truncate group-hover:text-white transition-colors">
            {item.title}
          </span>
          <span className="text-white/30 group-hover:text-white/60 transition-colors flex-shrink-0">↗</span>
        </a>
      ))}
    </div>
  );
};

export default AnimatedList;
