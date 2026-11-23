import { useState, type ReactNode } from 'react'
import { KioskLanguageContext,type KioskLanguage } from './kioskLanguage'
export default function KioskLanguageProvider({children}:{children:ReactNode}){
 const [language,setLanguage]=useState<KioskLanguage>('en')
 return <KioskLanguageContext.Provider value={{language,setLanguage}}>{children}</KioskLanguageContext.Provider>
}
