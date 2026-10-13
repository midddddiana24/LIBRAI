import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'ai.librai.kiosk',
  appName: 'LIBRAI Kiosk',
  webDir: 'dist',
  android: { allowMixedContent: false },
}

export default config
