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
  responseType?: string
  language?: string
  account?: { loans: { book_title: string; due_at: string; can_renew: boolean; renewal_note: string }[]; unpaid_fine_cents: number } | null
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
  onRead: (text: string, language?: string) => void
  onStop: () => void
  onAccount: () => void
  onFeedback: (id: number, helpful: boolean) => void
}

const starters = ['Explain databases simply', 'Find beginner Python books', 'I need research help', 'How many books can I borrow?']

export default function KioskChat(props: Props) {
  const log = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight
  }, [props.turns])

  return <section className="library-chat" aria-label="LIBRAI library chatbot">
    <div className="chat-toolbar"><span><BookOpen aria-hidden="true" /> Library assistant</span><button type="button" disabled={props.busy || !props.turns.length} onClick={props.onClear}>Start a new question</button></div>
    <div className="chat-log" role="log" aria-label="Chat messages" aria-live="polite" aria-relevant="additions text" tabIndex={0} ref={log}>
      <div className="chat-welcome"><img src="/images/librai-symbol-v2.png" alt="" /><div><h2>Let’s work through it.</h2><p>Ask a study question, find a book, or get library help. English or Filipino is welcome.</p></div></div>
      {!props.turns.length && <div className="chat-starters">{starters.map(question => <button key={question} type="button" disabled={props.busy || props.offline} onClick={() => props.onAsk(question)}>{question}</button>)}</div>}
      {props.turns.map(turn => <div className="chat-turn" key={turn.id}>
        <article className="chat-message chat-message-user" aria-label="Your message"><strong>You</strong><p>{turn.question}</p></article>
        <article className="chat-message chat-message-assistant" aria-label="LIBRAI reply"><strong>LIBRAI</strong>
          {turn.status === 'pending' ? <p className="chat-thinking"><LoaderCircle className="loading-spinner" aria-hidden="true" /> Preparing your answer...</p> : <>
            <small className="chat-answer-source">{turn.responseType === 'account' ? 'Verified account lookup' : turn.responseType === 'policy' ? 'Library settings and procedures' : turn.responseType === 'catalog' ? 'Library catalog' : turn.responseType === 'clarify' ? 'A quick question' : 'AI study assistant'}</small>
            <p>{turn.answer}</p>
            {turn.fallback && <small>{turn.responseType === 'catalog' ? 'AI ranking is unavailable. Showing catalog matches using local search.' : 'Conversational AI could not respond. You can retry your message.'}</small>}
            {turn.account && <div className="chat-account-loans">{turn.account.loans.map((loan, index) => <div key={index}><strong>{loan.book_title}</strong><span>{turn.language === 'en' ? 'Due' : 'Due date'}: {new Intl.DateTimeFormat(turn.language === 'en' ? 'en-PH' : 'fil-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(loan.due_at))}</span><small>{loan.renewal_note}</small></div>)}</div>}
            {turn.responseType === 'account' && <button type="button" disabled={props.busy} onClick={props.onAccount}>Open My account</button>}
            {turn.books.length > 0 && <div className="chat-books">{turn.books.map(book => <button type="button" key={book.id} disabled={props.busy} onClick={() => props.onBook(book.id)}><BookOpen aria-hidden="true" /><span><strong>{book.title}</strong><span>{book.author}</span><small>{book.available_copies || 0} available / {book.shelf_location || 'Ask the librarian'}</small></span></button>)}</div>}
            {turn.status === 'failed' ? <button type="button" disabled={props.busy || props.offline} onClick={() => props.onAsk(turn.question)}>Retry message</button> : <div className="chat-reply-actions"><button type="button" onClick={() => props.speaking ? props.onStop() : props.onRead(turn.answer, turn.language)}>{props.speaking ? <VolumeX aria-hidden="true" /> : <Volume2 aria-hidden="true" />}{props.speaking ? 'Stop reading' : 'Read answer aloud'}</button>{turn.interactionId && (turn.feedback !== undefined ? <small>Thank you for your feedback.</small> : <div><span>Helpful?</span><button type="button" disabled={props.busy} onClick={() => props.onFeedback(turn.id, true)} aria-label="This reply was helpful">Yes</button><button type="button" disabled={props.busy} onClick={() => props.onFeedback(turn.id, false)} aria-label="This reply was not helpful">No</button></div>)}</div>}
          </>}
        </article>
      </div>)}
    </div>
    <div className="chat-composer">
      {props.topic && <p className="chat-context">Current topic: {props.topic}</p>}
      <form onSubmit={event => { event.preventDefault(); props.onAsk(props.query) }}><label htmlFor="ai-query">Message LIBRAI</label><div><input id="ai-query" value={props.query} maxLength={1000} onChange={event => props.onQuery(event.target.value)} placeholder="Ask a question or describe what you need" autoComplete="off" /><button className="primary" disabled={props.busy || props.offline || props.query.trim().length < 2}><Send aria-hidden="true" />Send</button></div></form>
      <VoiceControl key={props.sessionKey} label="Dictate question" disabled={props.busy || props.offline} onTranscript={props.onQuery} />
      <p className="chat-privacy">{props.personalized ? 'Your verified ID enables account help.' : 'Scan your ID in My account for personal help.'} Recent messages go to the AI provider; account results are excluded. Chat clears at session end. Library interaction records may be retained.</p>
    </div>
  </section>
}
