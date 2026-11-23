import { createContext, useContext } from 'react'
export type KioskLanguage='en'|'fil'
export const KioskLanguageContext=createContext<{language:KioskLanguage;setLanguage:(language:KioskLanguage)=>void}>({language:'en',setLanguage:()=>{}})
export function useKioskLanguage(){const value=useContext(KioskLanguageContext);return {...value,t:(en:string,fil:string)=>value.language==='fil'?fil:en}}
