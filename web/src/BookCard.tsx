import { useState } from 'react'
import { mediaUrl,type Book } from './api'
import { useKioskLanguage } from './kioskLanguage'
export default function BookCard({book,onOpen,disabled=false}:{book:Book;onOpen:()=>void;disabled?:boolean}){
 const [failed,setFailed]=useState(false),{t}=useKioskLanguage()
 const cover=mediaUrl(book.cover_url||book.cover_image)
 return <button className="book-card" disabled={disabled} onClick={onOpen}>{cover&&!failed?<img src={cover} alt="" loading="lazy" onError={()=>setFailed(true)}/>:<div className="cover-placeholder" aria-hidden="true">{book.title.split(/\s+/).slice(0,2).map(word=>word[0]).join('').toUpperCase()}</div>}<strong>{book.title}</strong><span>{book.author}</span><small className={`book-stock ${(book.available_copies||0)>0?'is-available':'is-unavailable'}`}>{book.available_copies||0} {t('available','available')}</small><small>{t('Shelf','Shelf')}: {book.shelf_location||t('Ask the librarian','Magtanong sa librarian')}</small></button>
}
