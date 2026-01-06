# Modern UI Design - DHCS BHT Demo

**Design Philosophy**: Clean, professional, AI-first interface inspired by Perplexity, Claude, and Grok

## Design Principles

1. **Minimalist**: Remove visual clutter, focus on content
2. **Dark Mode First**: Modern, reduces eye strain during demos
3. **Streaming Responses**: Show AI thinking in real-time
4. **Source Citations**: Build trust with data references
5. **Mobile-Responsive**: Works on tablets for field demos
6. **Fast Loading**: < 2 second initial load

## Visual Style Guide

### Color Palette

**Dark Mode (Primary)**:
```css
:root {
  /* Backgrounds */
  --bg-primary: #0F0F0F;        /* Main background (almost black) */
  --bg-secondary: #1A1A1A;      /* Cards, panels */
  --bg-tertiary: #242424;       /* Hover states */
  --bg-input: #2A2A2A;          /* Input fields */

  /* Text */
  --text-primary: #ECECEC;      /* Main text */
  --text-secondary: #A0A0A0;    /* Subtext, labels */
  --text-muted: #707070;        /* Placeholder, disabled */

  /* Accent */
  --accent-primary: #3B82F6;    /* Blue - primary actions */
  --accent-hover: #2563EB;      /* Darker blue */
  --accent-success: #10B981;    /* Green - success states */
  --accent-warning: #F59E0B;    /* Amber - warnings */
  --accent-danger: #EF4444;     /* Red - high risk */

  /* Borders */
  --border-subtle: #2A2A2A;     /* Dividers */
  --border-focus: #3B82F6;      /* Focus rings */
}
```

**Light Mode (Secondary)**:
```css
:root[data-theme="light"] {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8F8F8;
  --bg-tertiary: #F0F0F0;
  --bg-input: #FAFAFA;

  --text-primary: #1A1A1A;
  --text-secondary: #525252;
  --text-muted: #9CA3AF;

  /* Accents stay the same */
}
```

### Typography

```css
/* Font Stack */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  letter-spacing: -0.011em;
  -webkit-font-smoothing: antialiased;
}

/* Headings */
h1 { font-size: 32px; font-weight: 600; letter-spacing: -0.02em; }
h2 { font-size: 24px; font-weight: 600; letter-spacing: -0.015em; }
h3 { font-size: 18px; font-weight: 600; }

/* Code */
code {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
  font-size: 14px;
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
}
```

## Layout Structure

### Main Interface (Chat-Style)

```
┌─────────────────────────────────────────────────────────────┐
│  [DHCS Logo]    Behavioral Health Triage Assistant    [⚙️🌙] │  ← Header (60px)
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  👤 You:                                            │     │
│  │  How many high-risk events in Los Angeles today?   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  🤖 Assistant:  [Thinking...] ████░░░░              │     │
│  │                                                      │     │
│  │  I found **47 high-risk events** in Los Angeles    │     │
│  │  County today (last 24 hours).                      │     │
│  │                                                      │     │
│  │  Breakdown:                                          │     │
│  │  • Imminent risk: 12 cases                          │     │
│  │  • High risk: 35 cases                              │     │
│  │                                                      │     │
│  │  Top presenting problems:                            │     │
│  │  1. Suicidal ideation (23)                          │     │
│  │  2. Psychotic symptoms (14)                         │     │
│  │  3. Substance withdrawal (10)                       │     │
│  │                                                      │     │
│  │  ┌─────────────────────────────────────────┐       │     │
│  │  │ 📊 Data Sources                          │       │     │
│  │  │ • Pinot query (217ms)                    │       │     │
│  │  │ • Time range: 2024-01-03 00:00 - 23:59  │       │     │
│  │  │ [View Query] [Export Data]               │       │     │
│  │  └─────────────────────────────────────────┘       │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  💬 Ask about crisis events, analytics, or trends...    [→] │  ← Input (80px)
└─────────────────────────────────────────────────────────────┘
```

### Alternative: Dashboard-Style (for Stakeholders)

```
┌─────────────────────────────────────────────────────────────┐
│ [DHCS Logo] BHT Multi-Agent Dashboard        [Chat] [⚙️🌙]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 🔥 Active    │  │ ⚠️ High Risk │  │ ⏱️ Avg Wait  │         │
│  │ Events       │  │ Cases        │  │ Time         │         │
│  │ **1,247**    │  │ **89**       │  │ **12 min**   │         │
│  │ ↑ 23% today  │  │ ↑ 15% today  │  │ ↓ 8% today   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  AI Chat Assistant                                  │     │
│  │  ┌──────────────────────────────────────────────┐  │     │
│  │  │ 💬 Type a question or select a quick action  │  │     │
│  │  └──────────────────────────────────────────────┘  │     │
│  │                                                      │     │
│  │  Quick Actions:                                     │     │
│  │  [Analyze Surge] [Triage High-Risk] [County Stats] │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌──────────────────────────┐  ┌─────────────────────┐     │
│  │ 📈 Events by County       │  │ 🏥 Channel Mix       │     │
│  │ [Interactive Map]         │  │ [Pie Chart]          │     │
│  └──────────────────────────┘  └─────────────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Library

### 1. Message Bubble (User)

```tsx
// components/UserMessage.tsx
interface UserMessageProps {
  content: string;
  timestamp: Date;
}

export const UserMessage = ({ content, timestamp }: UserMessageProps) => (
  <div className="flex justify-end mb-4">
    <div className="bg-accent-primary/10 border border-accent-primary/20 rounded-2xl px-4 py-3 max-w-[80%]">
      <p className="text-text-primary">{content}</p>
      <span className="text-xs text-text-muted mt-1 block">
        {timestamp.toLocaleTimeString()}
      </span>
    </div>
  </div>
);
```

### 2. Message Bubble (Assistant with Streaming)

```tsx
// components/AssistantMessage.tsx
interface AssistantMessageProps {
  content: string;
  isStreaming: boolean;
  sources?: Array<{ type: string; query: string; duration: number }>;
}

export const AssistantMessage = ({ content, isStreaming, sources }: AssistantMessageProps) => (
  <div className="flex items-start gap-3 mb-4">
    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-primary to-accent-hover flex items-center justify-center flex-shrink-0">
      <span className="text-white text-sm">🤖</span>
    </div>

    <div className="flex-1 bg-bg-secondary rounded-2xl px-4 py-3">
      {/* Streaming Indicator */}
      {isStreaming && (
        <div className="flex items-center gap-2 text-text-muted text-sm mb-2">
          <div className="w-2 h-2 bg-accent-primary rounded-full animate-pulse" />
          <span>Thinking...</span>
        </div>
      )}

      {/* Message Content */}
      <div className="prose prose-invert prose-sm max-w-none">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>

      {/* Sources */}
      {sources && sources.length > 0 && (
        <div className="mt-4 p-3 bg-bg-tertiary rounded-lg border border-border-subtle">
          <div className="text-xs text-text-secondary font-medium mb-2">
            📊 Data Sources
          </div>
          {sources.map((source, idx) => (
            <div key={idx} className="text-xs text-text-muted flex items-center justify-between">
              <span>• {source.type}</span>
              <span className="text-accent-success">{source.duration}ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  </div>
);
```

### 3. Input Field (Chat-style)

```tsx
// components/ChatInput.tsx
export const ChatInput = ({ onSend, isLoading }: ChatInputProps) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      onSend(message);
      setMessage('');
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-bg-primary border-t border-border-subtle">
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex items-center gap-3 bg-bg-secondary rounded-full px-4 py-2 border border-border-subtle focus-within:border-accent-primary transition">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about crisis events, analytics, or trends..."
            className="flex-1 bg-transparent border-none outline-none text-text-primary placeholder:text-text-muted"
            disabled={isLoading}
          />

          <button
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            className="w-8 h-8 rounded-full bg-accent-primary hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <span className="text-white">→</span>
            )}
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 mt-3 overflow-x-auto">
          <QuickAction onClick={() => setMessage("Show high-risk events in the last hour")}>
            ⚠️ High-Risk Events
          </QuickAction>
          <QuickAction onClick={() => setMessage("Analyze surge patterns")}>
            📈 Surge Analysis
          </QuickAction>
          <QuickAction onClick={() => setMessage("Triage cases by county")}>
            🗺️ County Triage
          </QuickAction>
          <QuickAction onClick={() => setMessage("What are the top presenting problems?")}>
            🧠 Top Problems
          </QuickAction>
        </div>
      </div>
    </div>
  );
};

const QuickAction = ({ children, onClick }: { children: React.ReactNode; onClick: () => void }) => (
  <button
    onClick={onClick}
    className="px-3 py-1.5 bg-bg-tertiary hover:bg-bg-input text-text-secondary text-sm rounded-full whitespace-nowrap transition"
  >
    {children}
  </button>
);
```

### 4. Stat Card (for Dashboard)

```tsx
// components/StatCard.tsx
interface StatCardProps {
  icon: string;
  label: string;
  value: string;
  change?: { value: number; trend: 'up' | 'down' };
  variant?: 'default' | 'danger' | 'success';
}

export const StatCard = ({ icon, label, value, change, variant = 'default' }: StatCardProps) => {
  const variantColors = {
    default: 'border-border-subtle',
    danger: 'border-accent-danger/30 bg-accent-danger/5',
    success: 'border-accent-success/30 bg-accent-success/5'
  };

  return (
    <div className={`bg-bg-secondary border ${variantColors[variant]} rounded-xl p-4 hover:border-accent-primary/30 transition cursor-pointer`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-text-secondary text-sm">{label}</span>
      </div>

      <div className="text-3xl font-semibold text-text-primary mb-1">
        {value}
      </div>

      {change && (
        <div className={`text-xs ${change.trend === 'up' ? 'text-accent-danger' : 'text-accent-success'} flex items-center gap-1`}>
          <span>{change.trend === 'up' ? '↑' : '↓'}</span>
          <span>{Math.abs(change.value)}% today</span>
        </div>
      )}
    </div>
  );
};
```

### 5. Header with Theme Toggle

```tsx
// components/Header.tsx
export const Header = () => {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <header className="fixed top-0 left-0 right-0 bg-bg-primary/80 backdrop-blur-xl border-b border-border-subtle z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-accent-hover rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          <div>
            <h1 className="text-text-primary font-semibold text-lg">
              DHCS BHT Assistant
            </h1>
            <p className="text-text-muted text-xs">
              Behavioral Health Triage • Powered by AI
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="w-10 h-10 rounded-full bg-bg-secondary hover:bg-bg-tertiary transition flex items-center justify-center"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>

          <button className="w-10 h-10 rounded-full bg-bg-secondary hover:bg-bg-tertiary transition flex items-center justify-center">
            ⚙️
          </button>
        </div>
      </div>
    </header>
  );
};
```

## Animations & Micro-interactions

### Streaming Text Effect

```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-enter {
  animation: fadeInUp 0.3s ease-out;
}

.typing-indicator {
  display: inline-block;
}

.typing-indicator::after {
  content: '█';
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
```

### Hover Effects

```css
/* Cards */
.card {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -12px rgba(59, 130, 246, 0.2);
}

/* Buttons */
.button {
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
}

.button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  transform: translate(-50%, -50%);
  transition: width 0.3s, height 0.3s;
}

.button:hover::before {
  width: 300px;
  height: 300px;
}
```

## Responsive Breakpoints

```css
/* Tailwind-style breakpoints */
/* Mobile: < 640px */
/* Tablet: 640px - 1024px */
/* Desktop: > 1024px */

@media (max-width: 640px) {
  /* Stack cards vertically */
  .stats-grid {
    grid-template-columns: 1fr;
  }

  /* Full-width chat */
  .chat-container {
    max-width: 100%;
    padding: 0 1rem;
  }

  /* Smaller header */
  header h1 {
    font-size: 16px;
  }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1025px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

## Tech Stack

### Frontend Framework
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "typescript": "^5.3.0",

    "tailwindcss": "^3.4.0",
    "framer-motion": "^11.0.0",
    "react-markdown": "^9.0.0",

    "axios": "^1.6.0",
    "swr": "^2.2.0",

    "recharts": "^2.10.0",
    "lucide-react": "^0.300.0"
  }
}
```

### Build Setup

```bash
# Create Next.js app
npx create-next-app@latest ui-modern --typescript --tailwind --app

cd ui-modern

# Install additional dependencies
npm install framer-motion react-markdown recharts lucide-react axios swr

# Configure Tailwind with custom colors
# (see tailwind.config.ts below)
```

### Tailwind Config

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: 'var(--bg-primary)',
          secondary: 'var(--bg-secondary)',
          tertiary: 'var(--bg-tertiary)',
          input: 'var(--bg-input)',
        },
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
        },
        accent: {
          primary: 'var(--accent-primary)',
          hover: 'var(--accent-hover)',
          success: 'var(--accent-success)',
          warning: 'var(--accent-warning)',
          danger: 'var(--accent-danger)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          focus: 'var(--border-focus)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Cascadia Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
export default config
```

## API Integration

### Chat Hook with Streaming

```typescript
// hooks/useChat.ts
import { useState, useCallback } from 'react';
import axios from 'axios';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{ type: string; query: string; duration: number }>;
}

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
        message: content,
      });

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
        sources: response.data.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { messages, sendMessage, isLoading };
};
```

### Real-time Stats Hook

```typescript
// hooks/useStats.ts
import useSWR from 'swr';
import axios from 'axios';

const fetcher = (url: string) => axios.get(url).then(res => res.data);

export const useStats = () => {
  const { data, error } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/stats`,
    fetcher,
    { refreshInterval: 30000 } // Refresh every 30 seconds
  );

  return {
    stats: data,
    isLoading: !error && !data,
    isError: error,
  };
};
```

## Performance Optimizations

### 1. Code Splitting
```typescript
// Lazy load heavy components
import dynamic from 'next/dynamic';

const ChartComponent = dynamic(() => import('./Chart'), {
  loading: () => <div>Loading chart...</div>,
  ssr: false,
});
```

### 2. Image Optimization
```typescript
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="DHCS Logo"
  width={40}
  height={40}
  priority
/>
```

### 3. Font Optimization
```typescript
// app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});
```

## Accessibility

```typescript
// Ensure all interactive elements are keyboard accessible
<button
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  aria-label="Send message"
  className="..."
>
  →
</button>

// Add ARIA labels
<div role="status" aria-live="polite" aria-atomic="true">
  {isLoading && 'Loading...'}
</div>

// Keyboard shortcuts
useEffect(() => {
  const handleKeyboard = (e: KeyboardEvent) => {
    if (e.metaKey && e.key === 'k') {
      focusSearchInput();
    }
  };

  window.addEventListener('keydown', handleKeyboard);
  return () => window.removeEventListener('keydown', handleKeyboard);
}, []);
```

## Demo Script

### Opening Screen (First Load)
1. Show clean, minimal interface
2. Display welcome message: "Welcome to DHCS Behavioral Health Triage Assistant"
3. Show 4 quick action buttons:
   - "Analyze high-risk events"
   - "View county statistics"
   - "Detect surge patterns"
   - "Get recommendations"

### Demo Flow for Stakeholders
1. **Click "Analyze high-risk events"**
   - Show streaming response
   - Display data sources
   - Render risk breakdown

2. **Ask follow-up: "Show me trends for Los Angeles"**
   - Demonstrate contextual awareness
   - Show county-specific data
   - Include time-series chart

3. **Switch to dashboard view**
   - Show real-time stats
   - Display geographic heat map
   - Demonstrate auto-refresh

4. **Toggle dark/light mode**
   - Smooth transition
   - Show professional appearance in both modes

5. **Mobile view** (if presenting on tablet)
   - Responsive layout
   - Touch-friendly interactions

## Build & Deploy

```bash
# Build for production
npm run build

# Test production build locally
npm run start

# Deploy to S3 (see AWS_MINIMAL_DEPLOYMENT.md)
./deployment/deploy-ui.sh
```

## Comparison to Inspiration

| Feature | Perplexity | Claude | Grok | Our Design |
|---------|-----------|--------|------|------------|
| **Dark Mode** | ✅ Default | ✅ Default | ✅ Default | ✅ Default |
| **Streaming** | ✅ | ✅ | ✅ | ✅ |
| **Source Citations** | ✅ Inline | ✅ Footer | ❌ | ✅ Collapsible |
| **Quick Actions** | ✅ | ❌ | ✅ | ✅ |
| **Mobile Responsive** | ✅ | ✅ | ✅ | ✅ |
| **Code Syntax Highlighting** | ✅ | ✅ | ❌ | ✅ |
| **Export Options** | ✅ | ❌ | ❌ | ✅ |
| **Real-time Stats** | ❌ | ❌ | ❌ | ✅ (BHT-specific) |

## Next Steps

1. Create React/Next.js project structure
2. Implement core components
3. Connect to API endpoints
4. Add loading states and error handling
5. Test on multiple devices/browsers
6. Deploy to S3/CloudFront
7. Gather stakeholder feedback
