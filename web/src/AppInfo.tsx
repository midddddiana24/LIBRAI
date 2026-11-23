import { useRef, useState } from 'react'
import { API_BASE } from './api'
import { useKioskLanguage } from './kioskLanguage'
export const APP_VERSION='1.9.2'
export const APP_BUILD=15
export default function AppInfo({online}:{online:boolean|null}){
 const [open,setOpen]=useState(false), dialog=useRef<HTMLDialogElement>(null)
 const {t}=useKioskLanguage()
 return <><button type="button" className="about-button" onClick={()=>{setOpen(true);dialog.current?.showModal()}}>{t('About LIBRAI','Tungkol sa LIBRAI')}</button><dialog ref={dialog} className="about-dialog" onClose={()=>setOpen(false)} aria-labelledby="about-title">{open&&<><h2 id="about-title">LIBRAI {APP_VERSION}</h2><dl><dt>{t('Client build','Build ng app')}</dt><dd>{APP_BUILD} · {window.location.protocol==='https:'&&window.location.hostname==='localhost'?'Android kiosk':'Web client'}</dd><dt>API</dt><dd>{API_BASE}</dd><dt>{t('Connection','Koneksyon')}</dt><dd>{online===null?t('Checking','Sinusuri'):online?t('Connected','Connected'):t('Unavailable','Hindi available')}</dd></dl><p>{t('The installed APK needs a manual update to receive new interface releases.','Kailangang i-update ang naka-install na APK para makuha ang bagong interface.')}</p><form method="dialog"><button autoFocus>{t('Close','Isara')}</button></form></>}</dialog></>
}
