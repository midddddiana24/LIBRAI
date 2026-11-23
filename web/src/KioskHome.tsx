import {useKioskLanguage} from './kioskLanguage'
import { ArrowUpRight, Volume2, UserRoundPlus } from 'lucide-react'
import LibraryActionIcon from './LibraryActionIcon'
import KioskTileArt from './KioskTileArt'
import VoiceControl from './VoiceControl'

type Props = {
  query: string
  busy: boolean
  online: boolean | null
  onSearch: (query: string) => void
  onBorrow: () => void
  onReturn: () => void
  onRegister: () => void
  onAccount: () => void
  onAssistant: () => void
  onDiscover: () => void
  onVoiceCommand: (text: string) => void
  onHearInstructions: () => void
}

export default function KioskHome({ query, busy, online, onSearch, onBorrow, onReturn, onRegister, onAccount, onAssistant, onDiscover, onVoiceCommand, onHearInstructions }: Props) {
  const {t}=useKioskLanguage()
  const unavailable = busy || online === false

  return <div className="kiosk-home kiosk-menu">
    <div className="kiosk-menu-screen">
      <section className="kiosk-intro" aria-labelledby="kiosk-intro-title">
        <div><h1 id="kiosk-intro-title">{t('Welcome to your library.','Maligayang pagdating.')}</h1><p>{t('What would you like to do today?','Ano ang nais mong gawin ngayon?')}</p></div>
        <div className="kiosk-home-tools">
          <button className="hear-instructions" type="button" onClick={onHearInstructions}><Volume2 aria-hidden="true" /><span>{t('Hear instructions','Pakinggan ang gabay')}</span></button>
          <VoiceControl label={t('Voice command','Voice command')} disabled={unavailable} confirmBeforeUse onTranscript={onVoiceCommand} />
        </div>
      </section>

      <section className="kiosk-task-grid" aria-label="Library services">
        <button className="kiosk-task kiosk-task-borrow" type="button" aria-label={t('Borrow a book','Humiram ng libro')} disabled={unavailable} onClick={onBorrow}>
          <span className="kiosk-task-icon"><KioskTileArt kind="borrow" /></span>
          <strong>{t('Borrow a book','Humiram ng libro')}</strong>
          <span className="kiosk-task-hint">{t('Scan your ID and book.','I-scan ang ID at libro.')}</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
        <button className="kiosk-task kiosk-task-return" type="button" aria-label={t('Return a book','Magsauli ng libro')} disabled={unavailable} onClick={onReturn}>
          <span className="kiosk-task-icon"><KioskTileArt kind="return" /></span>
          <strong>{t('Return a book','Magsauli ng libro')}</strong>
          <span className="kiosk-task-hint">{t('Bring a book back.','Isauli ang hiniram.')}</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
        <button className="kiosk-task kiosk-task-find" type="button" aria-label={t('Find a book','Maghanap ng libro')} disabled={unavailable} onClick={() => onSearch(query)}>
          <span className="kiosk-task-icon"><KioskTileArt kind="find" /></span>
          <strong>{t('Find a book','Maghanap ng libro')}</strong>
          <span className="kiosk-task-hint">{t('Search the library catalog.','Maghanap sa catalog.')}</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
        <button className="kiosk-task kiosk-task-discover" type="button" aria-label={t('Discover books','Tumuklas ng libro')} disabled={unavailable} onClick={onDiscover}>
          <span className="kiosk-task-icon"><KioskTileArt kind="discover" /></span>
          <strong>{t('Discover books','Tumuklas ng libro')}</strong>
          <span className="kiosk-task-hint">{t('Find your next good read.','Piliin ang susunod na babasahin.')}</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
      </section>

      <section className="kiosk-quick-links" aria-label="More ways to use the library">
          <button disabled={unavailable} onClick={onRegister}><UserRoundPlus aria-hidden="true" />{t('Register','Magparehistro')}</button>
          <button disabled={unavailable} onClick={onAccount}><LibraryActionIcon kind="account" />{t('My account','Account ko')}</button>
          <button disabled={unavailable} onClick={onAssistant}><LibraryActionIcon kind="assistant" />Ask LIBRAI</button>
      </section>
    </div>
  </div>
}
