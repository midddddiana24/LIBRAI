import assert from 'node:assert/strict'
import {chromium} from 'playwright-core'
const base=process.env.DESIGN_UI_URL||'http://127.0.0.1:4190'
const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true})
try{
 for(const [width,height] of [[320,740],[600,960],[768,1024],[960,600]]){
  const p=await b.newPage({viewport:{width,height},reducedMotion:'reduce'})
  let mutations=0
  const book={id:1,title:'Sample Library Book',author:'Sample Author',available_copies:2,shelf_location:'A-01',cover_url:'/images/librai-symbol-v2.png'}
  await p.route(/\/health$|\/api\/v1\//,r=>{const url=new URL(r.request().url());if(r.request().method()==='POST')mutations++
   if(url.pathname.endsWith('/registrations'))return r.fulfill({status:422,json:{detail:[{loc:['body','student_id'],msg:'This campus ID is already registered.'}]}})
   return r.fulfill({json:url.pathname==='/health'?{status:'healthy'}:url.pathname.endsWith('/ai/recommend')?[book]:{items:[book],total:1}})
  })
  await p.goto(base);await p.getByRole('button',{name:'Borrow a book',exact:true}).waitFor()
  await p.getByLabel('Library options',{exact:true}).click()
  await p.getByLabel('Interface language',{exact:true}).selectOption('fil')
  await p.getByRole('button',{name:'Humiram ng libro',exact:true}).waitFor()
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth),width)
  if(width>=600)assert.ok(await p.evaluate(()=>document.documentElement.scrollHeight<=innerHeight+1),'Translated tablet home fits vertically')
  await p.getByLabel('Interface language',{exact:true}).selectOption('en')
  await p.getByRole('button',{name:'About LIBRAI',exact:true}).click()
  await p.getByRole('heading',{name:'LIBRAI 1.9.3'}).waitFor()
  await p.getByRole('button',{name:'Close',exact:true}).click()
  await p.getByLabel('Library options',{exact:true}).press('Escape')
  assert.equal(await p.locator('.utility-menu').evaluate(el=>el.open),false)
  assert.equal(await p.getByLabel('Library options',{exact:true}).evaluate(el=>el===document.activeElement),true)
  await p.mouse.move(0,0)
  if(width===768)await p.screenshot({path:'../generated/ux-1.9-kiosk.png',fullPage:true})
  assert.equal(mutations,0,'Language and About must not write library data')
  await p.getByRole('button',{name:'Discover books',exact:true}).click();await p.locator('.book-card img').waitFor()
  await p.getByText('Shelf: A-01',{exact:true}).waitFor()
  await p.getByRole('button',{name:'Home',exact:true}).click()
  if(width===768){
   await p.getByRole('button',{name:'Register',exact:true}).click()
   for(const [name,value]of Object.entries({student_id:'TEST-01',first_name:'Sample',last_name:'Reader',course:'BSIT',year_level:'1',email:'sample@example.invalid'}))await p.locator(`[name=${name}]`).fill(value)
   await p.getByRole('checkbox',{name:/These are my details/}).check()
   await p.getByRole('button',{name:'Submit for staff approval',exact:true}).click()
   await p.locator('[name=student_id][aria-invalid=true]').waitFor()
   assert.equal(await p.locator('[name=first_name]').inputValue(),'Sample')
   await p.getByText('This campus ID is already registered.',{exact:true}).last().waitFor()
  }
  console.log('PASS shared UX',width,height,'language, About, cover, scoped error recovery')
  await p.close()
 }
}finally{await b.close()}
