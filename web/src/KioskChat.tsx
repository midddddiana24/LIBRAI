import { useEffect, useRef } from 'react'
import { BookOpen, LoaderCircle, Send, Volume2, VolumeX } from 'lucide-react'
import type { Book } from './api'
import VoiceControl from './VoiceControl'
import './kiosk-chat.css'

export type ChatTurn = {
  id: number
  question: string
  answer: string
  books: Book[]
  status: 'pending' | 'done' | 'failed'
  fallback?: boolean
  interactionId?: number
  feedback?: boolean
}

type Props = {
  turns: ChatTurn[]
  query: string
  busy: boolean
  offline: boolean
  personalized: boolean
  topic: string
  sessionKey: number
  speaking: boolean
  onQuery: (query: string) => void
  onAsk: (query: string) => void
  onClear: () => void
  onBook: (id: number) => void
  onRead: (text: string) => void
  onStop: () => void
  onFeedback: (id: number, helpful: boolean) => void
}

const starters = ['Find beginner Python books', 'How many books can I borrow?', 'How do I register?']

export default function KioskChat(props: Props) {
  const log = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight
  }, [props.turns])

  return <section className="library-chat" aria-label="LIBRAI library chatbot">
    <div className="chat-toolbar"><span><BookOpen aria-hidden="true" /> Library assistant</span><button type="button" disabled={props.busy || !props.turns.length} onClick={props.onClear}>Start a new question</button></div>
    <div className="chat-log" role="log" aria-label="Chat messages" aria-live="polite" aria-relevant="additions text" tabIndex={0} ref={log}>
      <div className="chat-welcome"><img src="/images/librai-symbol-v2.png" alt="" /><div><h2>What can I help you find?</h2><p>Ask about books, borrowing, or your next library visit.</p></div></div>
      {!props.turns.length && <div className="chat-starters">{starters.map(question => <button key={question} type="button" disabled={props.busy || props.offline} onClick={() => props.onAsk(question)}>{question}</button>)}</div>}
      {props.turns.map(turn => <div className="chat-turn" key={turn.id}>
        <article className="chat-message chat-message-user" aria-label="Your message"><strong>You</strong><p>{turn.question}</p></article>
        <article className="chat-message chat-message-assistant" aria-label="LIBRAI reply"><strong>LIBRAI</strong>
          {turn.status === 'pending' ? <p className="chat-thinking"><LoaderCircle className="loading-spinner" aria-hidden="true" /> Checking the library...</p> : <>
            <p>{turn.answer}</p>
            {turn.fallback && <small>AI ranking is unavailable. Showing catalog matches using local search.</small>}
            {turn.books.length > 0 && <div className="chat-books">{turn.books.map(book => <button type="button" key={book.id} disabled={props.busy} onClick={() => props.onBook(book.id)}><BookOpen aria-hidden="true" /><span><strong>{book.title}</strong><span>{book.author}</span><small>{book.available_copies || 0} available / {book.shelf_location || 'Ask the librarian'}</small></span></button>)}</div>}
            {turn.status === 'failed' ? <button type="button" disabled={props.busy || props.offline} onClick={() => props.onAsk(turn.question)}>Retry message</button> : <div className="chat-reply-actions"><button type="button" onClick={() => props.speaking ? props.onStop() : props.onRead(turn.answer)}>{props.speaking ? <VolumeX aria-hidden="true" /> : <Volume2 aria-hidden="true" />}{props.speaking ? 'Stop reading' : 'Read answer aloud'}</button>{turn.interactionId && (turn.feedback !== undefined ? <small>Thank you for your feedback.</small> : <div><span>Helpful?</span><button type="button" disabled={props.busy} onClick={() => props.onFeedback(turn.id, true)} aria-label="This reply was helpful">Yes</button><button type="button" disabled={props.busy} onClick={() => props.onFeedback(turn.id, false)} aria-label="This reply was not helpful">No</button></div>)}</div>}
          </>}
        </article>
      </div>)}
    </div>
    <div className="chat-composer">
      {props.topic && <p className="chat-context">Current topic: {props.topic}</p>}
      <form onSubmit={event => { event.preventDefault(); props.onAsk(props.query) }}><label htmlFor="ai-query">Message LIBRAI</label><div><input id="ai-query" value={props.query} maxLength={1000} onChange={event => props.onQuery(event.target.value)} placeholder="Ask about books or library services" autoComplete="off" /><button className="primary" disabled={props.busy || props.offline || props.query.trim().length < 2}><Send aria-hidden="true" />Send</button></div></form>
      <VoiceControl key={props.sessionKey} label="Dictate question" disabled={props.busy || props.offline} onTranscript={props.onQuery} />
      <p className="chat-privacy">{props.personalized ? 'Suggestions can use your borrowing history during this session.' : 'For personal suggestions, scan your ID in My account, then return here.'} This chat clears when the session ends. Library search records may be retained.</p>
    </div>
  </section>
}
