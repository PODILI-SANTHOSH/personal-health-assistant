import { useEffect, useState } from 'react'
import { Bot, SendHorizontal, Sparkles, Trash2 } from 'lucide-react'
import api from '../services/api'

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await api.get('/api/chat/history')
        const history = response.data.conversations || []
        if (history.length > 0) {
          const latest = history[history.length - 1]
          setConversationId(latest.conversation_id)
          setMessages(latest.messages || [])
        }
      } catch (error) {
        console.error(error)
      }
    }
    loadHistory()
  }, [])

  const sendQuestion = async () => {
    if (!input.trim()) return
    const question = input.trim()
    setInput('')
    setLoading(true)
    const userMsg = { role: 'user', content: question, created_at: new Date().toLocaleTimeString() }
    setMessages((current) => [...current, userMsg])

    try {
      const response = await api.post('/api/chat', { question, conversation_id: conversationId })
      const nextConversationId = response.data.conversation_id
      setConversationId(nextConversationId)
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: response.data.answer, created_at: new Date().toLocaleTimeString() },
      ])
      const sourceList = (response.data.sources || []).map((source) => ({
        source: source.source,
        section: source.section,
        snippet: source.snippet,
      }))
      if (sourceList.length) {
        setMessages((current) => [
          ...current,
          { role: 'assistant', content: `Sources: ${sourceList.map((source) => `${source.source} (${source.section})`).join(', ')}`, created_at: new Date().toLocaleTimeString() },
        ])
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: 'I hit an error while answering. Please check the backend and try again.', created_at: new Date().toLocaleTimeString() },
      ])
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const resetThread = () => {
    setMessages([])
    setConversationId(null)
  }

  return (
    <div className="flex h-[72vh] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-brand-50 p-2 text-brand-700"><Bot className="h-5 w-5" /></div>
          <div>
            <p className="text-sm text-slate-500">Assistant</p>
            <h2 className="font-semibold text-slate-800">Health support</h2>
          </div>
        </div>
        <button onClick={resetThread} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
          <Trash2 className="h-4 w-4" /> Reset
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
        {messages.length === 0 && !loading ? (
          <div className="rounded-2xl bg-slate-50 p-5 text-sm text-slate-600">
            Ask about symptoms, prevention, or general wellness. The assistant will use the indexed medical sources and safety guidance to craft a response.
          </div>
        ) : null}

        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl rounded-2xl px-4 py-3 ${message.role === 'user' ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-700'}`}>
              <p className="whitespace-pre-wrap leading-7">{message.content}</p>
              <p className={`mt-2 text-[10px] ${message.role === 'user' ? 'text-brand-100' : 'text-slate-500'}`}>{message.created_at}</p>
            </div>
          </div>
        ))}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Sparkles className="h-4 w-4 animate-pulse" /> Reviewing the knowledge base...
          </div>
        ) : null}
      </div>

      <div className="border-t border-slate-200 p-4">
        <div className="flex gap-3">
          <textarea
            rows={2}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                sendQuestion()
              }
            }}
            className="w-full resize-none rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-700 outline-none ring-0 transition focus:border-brand-500"
            placeholder="Ask a health question..."
          />
          <button onClick={sendQuestion} className="inline-flex items-center justify-center rounded-2xl bg-brand-600 p-4 text-white transition hover:bg-brand-700 disabled:opacity-50" disabled={loading || !input.trim()}>
            <SendHorizontal className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
