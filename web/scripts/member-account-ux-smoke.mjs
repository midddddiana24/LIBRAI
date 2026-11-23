import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { createServer, transformWithOxc } from 'vite'
import react from '@vitejs/plugin-react'
import { chromium } from 'playwright-core'

// Component-only synthetic fixtures. No backend, secrets, email, OCR processing, or live data.
const root = fileURLToPath(new URL('../', import.meta.url))
const source = `
import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import AccountPanel from '/src/AccountPanel.tsx'
import MemberForm from '/src/MemberForm.tsx'
import '/src/index.css'
import '/src/library-modern.css'
function Harness() {
 const [language,setLanguage] = useState('en')
 const [fieldErrors,setErrors] = useState({})
 const [saved,setSaved] = useState(false)
 return <main><button onClick={()=>setLanguage(value=>value==='en'?'fil':'en')}>Toggle test language</button><button onClick={()=>setErrors({email:'Synthetic email rejection'})}>Inject field error</button><AccountPanel user={{id:1,student_id:'SYNTHETIC-ONLY',verification_token:'synthetic-local-only'}} language={language}/><MemberForm publicRegistration busy={false} language={language} fieldErrors={fieldErrors} onCancel={()=>{}} onSubmit={event=>{event.preventDefault();setSaved(true)}}/>{saved&&<p>Fixture submitted</p>}</main>
}
createRoot(document.getElementById('root')).render(<Harness/>);
`
const server = await createServer({root, configFile:false, envDir:false, plugins:[react(),{
 name:'synthetic-member-harness',
 resolveId(id) { if(id==='/__member-ux-test.tsx') return '\0member-ux-test.tsx' },
 async load(id) { if(id==='\0member-ux-test.tsx') return (await transformWithOxc(source,'member-ux-test.tsx',{lang:'tsx'})).code },
 configureServer(server) { server.middlewares.use('/__member-ux',async (_req,res)=>{
   const html=await server.transformIndexHtml('/__member-ux','<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><div id="root"></div><script type="module" src="/__member-ux-test.tsx"></script></body></html>')
   res.setHeader('Content-Type','text/html');res.end(html)
 }) },
}],define:{'import.meta.env.VITE_API_BASE_URL':JSON.stringify('http://synthetic.invalid/api/v1')},server:{host:'127.0.0.1',port:0}})
let browser
try {
 await server.listen()
 const base=`http://127.0.0.1:${server.httpServer.address().port}`
 browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true})
 const page=await browser.newPage({viewport:{width:768,height:1024},reducedMotion:'reduce'})
 const errors=[],requests=[]
 page.on('pageerror',error=>errors.push(error.message))
 await page.route('**/*',async route=>{
   const url=new URL(route.request().url())
   if(url.origin===base) return route.continue()
   assert.equal(url.origin,'http://synthetic.invalid','Unexpected external request')
   requests.push(url.pathname+url.search)
   const offset=Number(url.searchParams.get('offset')||0),limit=Number(url.searchParams.get('limit')||10)
   let body
   if(url.pathname.endsWith('/borrowings')) {
     const status=url.searchParams.get('status')
     if(status==='active') body={items:[{id:901,book_title:'Current synthetic loan',due_at:'2030-01-01',status:'active',can_renew:false}],total:1}
     else if(status==='overdue') body={items:[{id:902,book_title:'Overdue synthetic loan',due_at:'2020-01-01',status:'overdue',can_renew:false}],total:1}
     else body={items:Array.from({length:Math.min(limit,53-offset)},(_,i)=>({id:offset+i+1,book_title:'History fixture '+(offset+i+1),due_at:'2020-01-01',status:'returned',can_renew:false})),total:53}
   } else if(url.pathname.endsWith('/reservations')) body={items:Array.from({length:Math.min(limit,12-offset)},(_,i)=>({id:offset+i+1,book_title:'Reservation fixture '+(offset+i+1),status:'cancelled'})),total:12}
   else if(url.pathname.endsWith('/fines')) body={items:[],total:0}
   else if(url.pathname.endsWith('/notifications')) body=Array.from({length:12},(_,i)=>({id:i+1,message:'Notification fixture '+(i+1),is_read:true,created_at:'2026-01-01'}))
   else throw Error('Unexpected fixture endpoint '+url.pathname)
   return route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(body)})
 })
 await page.goto(`${base}/__member-ux`)
 await page.getByText('Current synthetic loan',{exact:true}).waitFor()
 await page.getByText('Overdue synthetic loan',{exact:true}).waitFor()
 assert.equal(await page.getByRole('tab',{name:'Active loans',exact:true}).getAttribute('aria-selected'),'true')
 assert.equal(await page.getByText('Renewal is unavailable. The server did not provide a reason; please ask library staff.',{exact:true}).count(),2)
 await page.getByRole('tab',{name:'History',exact:true}).click()
 await page.getByText('Showing 1–10 of 53 records',{exact:true}).waitFor()
 for(let i=0;i<5;i++) { await page.getByRole('button',{name:'Next',exact:true}).click(); await page.getByText(`Showing ${11+i*10}–${Math.min(20+i*10,53)} of 53 records`,{exact:true}).waitFor() }
 await page.getByText('History fixture 53',{exact:true}).waitFor()
 assert.ok(requests.some(url=>url.includes('offset=50')),'History beyond original limit must be reachable')
 await page.getByRole('tab',{name:'Reservations',exact:true}).click()
 await page.getByText('Showing 1–10 of 12 records',{exact:true}).waitFor()
 await page.getByRole('button',{name:'Next',exact:true}).click()
 await page.getByText('Reservation fixture 12',{exact:true}).waitFor()
 await page.getByRole('tab',{name:'Notifications',exact:true}).click()
 await page.getByText('Showing 1–10 of 12 records',{exact:true}).waitFor()
 await page.getByRole('button',{name:'Next',exact:true}).click()
 await page.getByText('Notification fixture 12',{exact:false}).waitFor()
 await page.getByRole('tab',{name:'Fines',exact:true}).click()
 await page.getByText('0 records',{exact:true}).waitFor()
 const form=page.locator('.member-form')
 assert.equal(await form.locator('fieldset').count(),4)
 await form.getByRole('button',{name:'Submit for staff approval',exact:true}).click()
 assert.equal(await form.locator('[name=student_id]').getAttribute('aria-invalid'),'true')
 for(const [name,value] of Object.entries({student_id:'TEST-ONLY',first_name:'Synthetic',last_name:'Fixture',course:'Test course',year_level:'2'})) await form.locator(`[name=${name}]`).fill(value)
 await form.locator('[name=email]').fill('bad-email');await form.locator('[name=email]').blur()
 await page.getByText('Enter a valid email address or leave this field blank.',{exact:true}).waitFor()
 await form.locator('[name=email]').fill('fixture@example.invalid')
 await page.getByRole('button',{name:'Inject field error',exact:true}).click()
 await page.getByText('Synthetic email rejection',{exact:true}).waitFor()
 assert.equal(await form.locator('[name=first_name]').inputValue(),'Synthetic')
 assert.ok(await form.locator('[name=email]').getAttribute('aria-describedby'))
 await form.locator('[name=email]').fill('')
 await form.getByLabel('These are my details, and I am submitting them for library staff review.',{exact:true}).check()
 await form.getByRole('button',{name:'Submit for staff approval',exact:true}).click()
 await page.getByText('Fixture submitted',{exact:true}).waitFor()
 await page.getByRole('button',{name:'Toggle test language',exact:true}).click()
 await page.getByRole('tab',{name:'Kasalukuyang hiram',exact:true}).waitFor()
 await form.getByLabel('Pangalan / gitnang inisyal',{exact:true}).waitFor()
 for(const width of [320,768,1024,1440]) { await page.setViewportSize({width,height:1024});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Horizontal overflow at ${width}px`) }
 assert.deepEqual(errors,[])
 console.log('PASS synthetic component UX: active/overdue, truthful renewal fallback, 53-row history, reservations/notifications pagination, empty fines, grouped registration, inline validation, retained inputs, optional email, Filipino labels, 320/768/1024/1440 widths; no backend or external traffic')
} finally { await browser?.close();await server.close() }
