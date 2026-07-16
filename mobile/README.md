# JARVIS OS - Mobile (Android / iOS)

JARVIS OS can be accessed on mobile devices via **Progressive Web App (PWA)** or built as a native app.

## Quick Start (PWA)

1. Connect your phone to the same WiFi network as your PC running JARVIS
2. Open `http://<your-pc-ip>:8000/console` in Chrome (Android) or Safari (iOS)
3. Tap **"Add to Home Screen"** — installs like a native app
4. Full voice console, skills, and HUD work on mobile

## PWA Features

- **Installable** — Add to home screen, launches fullscreen
- **Offline support** — Service worker caches core assets
- **Responsive UI** — Adapts to phone and tablet screens
- **Voice input** — Use microphone for voice commands
- **Push notifications** — Timer alerts and reminders (when configured)

## Native Mobile App (Future)

For a fully native experience, JARVIS OS can be wrapped with:

- **Capacitor** (Ionic) — Wrap the web app as native iOS/Android
- **React Native** — Native UI with JARVIS API backend
- **Tauri Mobile** — Rust-based mobile shell (alpha)

### Capacitor Setup (when ready)

```bash
npm install @capacitor/core @capacitor/cli
npx cap init "JARVIS OS" "dev.jarvis-ios.app"
npm install @capacitor/android @capacitor/ios
npx cap add android
npx cap add ios
npx cap sync
npx cap open android   # Opens Android Studio
npx cap open ios       # Opens Xcode
```

## Architecture

```
Mobile Device (PWA/Native App)
        │
        ▼
JARVIS OS Backend (FastAPI on PC)
        │
        ├── Skills Engine
        ├── Voice Service
        ├── Desktop Automation
        ├── Smart Home Control
        └── Vision/Camera
```

## Network Requirements

- **Same WiFi**: Phone and PC must be on the same network
- **IP Address**: Find your PC's IP with `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
- **Port**: Default port 8000 must be accessible (check firewall)

## Security Note

For remote access outside your local network:
- Use a VPN (WireGuard, Tailscale)
- Or set up a reverse proxy with HTTPS (nginx + Let's Encrypt)
- Never expose port 8000 directly to the internet without authentication
