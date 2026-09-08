# JS Vendor Files — Download Instructions

These files must be downloaded before first run (for offline demo).
Save each file to `core/static/js/`.

## Required for offline operation:

### 1. HTMX 2.x
```
URL: https://unpkg.com/htmx.org@2.0.2/dist/htmx.min.js
Save as: core/static/js/htmx.min.js
Size: ~50 KB
```
PowerShell: `Invoke-WebRequest -Uri "https://unpkg.com/htmx.org@2.0.2/dist/htmx.min.js" -OutFile "core\static\js\htmx.min.js"`

### 2. GSAP 3.12
```
URL: https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js
Save as: core/static/js/gsap.min.js
Size: ~70 KB
```
PowerShell: `Invoke-WebRequest -Uri "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" -OutFile "core\static\js\gsap.min.js"`

### 3. dotLottie Player
```
URL: https://unpkg.com/@dotlottie/player-component@2.7.12/dist/dotlottie-player.mjs
Save as: core/static/js/dotlottie-player.mjs
Size: ~200 KB
```
PowerShell: `Invoke-WebRequest -Uri "https://unpkg.com/@dotlottie/player-component@2.7.12/dist/dotlottie-player.mjs" -OutFile "core\static\js\dotlottie-player.mjs"`

## Quick download (run from C:\IP-SAKTI-Sahayak\):
```powershell
$base = "core\static\js"
Invoke-WebRequest "https://unpkg.com/htmx.org@2.0.2/dist/htmx.min.js"                                     -OutFile "$base\htmx.min.js"
Invoke-WebRequest "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"                        -OutFile "$base\gsap.min.js"
Invoke-WebRequest "https://unpkg.com/@dotlottie/player-component@2.7.12/dist/dotlottie-player.mjs"        -OutFile "$base\dotlottie-player.mjs"
Write-Host "All vendor JS downloaded."
```

## CDN fallbacks (app.js has these built-in for online-only mode):
- HTMX: https://unpkg.com/htmx.org@2.0.2/dist/htmx.min.js
- GSAP: https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js
- dotLottie: https://unpkg.com/@dotlottie/player-component@2.7.12/dist/dotlottie-player.mjs
