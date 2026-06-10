# WAHA Gateway — Satu Cakrawala

> WhatsApp Gateway untuk Chatbot Kampus Satu Cakrawala.
> WAHA bertugas sebagai **transport layer** antara WhatsApp dan Backend AI.

---

## Arsitektur

```
Mahasiswa
  ↓ chat via WhatsApp
WAHA Gateway (WhatsApp HTTP API)
  ↓ webhook event
Backend API (api.satucakrawala.ac.id)
  ↓ get_session()
AI Agent → RAG / MCP / Human Handoff
  ↓ response
Backend call WAHA POST /api/sendText
  ↓
Mahasiswa terima balasan di WhatsApp
```

**Scope WAHA**: Hanya gateway transport WhatsApp.  
**Bukan scope WAHA**: AI Agent, RAG, MCP, Validasi NIM, Session User, Human Handoff, Database.

---

## Akses

| Service | URL |
|---------|-----|
| **Dashboard** | `https://capacity-undertaken-flash-recommendation.trycloudflare.com/` |
| **API Base** | `https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/` |
| **Local** | `http://localhost:3001/api/` |

### Kredensial

| | Value |
|---|---|
| **API Key** (header `X-Api-Key`) | `4c94510d4aaf48bbb286aaeb65a0bcdf` |
| **Dashboard User** | `admin` |
| **Dashboard Password** | `SatuCakrawala2024!` |

> ⚠️ Quick Tunnel URL berubah kalau proses cloudflared mati.  
> Untuk production, gunakan Named Tunnel dengan domain sendiri.

---

## Manajemen WAHA

```bash
cd /home/mannn/satu-cakrawala/waha-gateway

# Start WAHA
docker compose up -d

# Stop WAHA
docker compose down

# Restart WAHA
docker compose restart

# Lihat logs
docker compose logs -f

# Update ke versi terbaru
docker compose pull && docker compose up -d

# Cek status container
docker ps --filter name=satu-cakrawala-waha
```

---

## Session WhatsApp

### Start Session & Generate QR

```bash
# Create dan start session (otomatis generate QR)
curl -X POST https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{"name": "default", "start": true}'
```

**Response:**
```json
{
  "name": "default",
  "status": "STARTING",
  "engine": {"engine": "WEBJS"}
}
```

### Get QR Code

```bash
# Download QR sebagai PNG
curl -X GET "https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/default/auth/qr" \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Accept: image/png" \
  -o qr-code.png
```

Lalu scan QR dengan WhatsApp HP: **Menu → Perangkat Tertaut → Tautkan Perangkat**

### Check Session Status

```bash
# List semua session
curl -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions
```

**Response:**
```json
[
  {
    "name": "default",
    "status": "WORKING",
    "me": {"id": "62812xxxxxxx@c.us", "name": "Satu Cakrawala Bot"},
    "engine": {"engine": "WEBJS"}
  }
]
```

**Status yang mungkin:**
| Status | Arti |
|--------|------|
| `STARTING` | Sedang inisialisasi |
| `SCAN_QR_CODE` | Menunggu scan QR |
| `WORKING` | Aktif dan siap menerima/mengirim pesan |
| `STOPPED` | Session berhenti |
| `DISCONNECTED` | Koneksi terputus |

### Stop Session

```bash
curl -X POST "https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions/default/stop" \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf"
```

### Logout Session

```bash
# Hapus session (perlu scan QR ulang)
curl -X DELETE "https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions/default" \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf"
```

### Restart Session (kalau WhatsApp logout)

```bash
# Stop dulu
curl -X POST "https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions/default/stop" \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf"

# Delete session lama
curl -X DELETE "https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions/default" \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf"

# Create ulang + start (akan generate QR baru)
curl -X POST "https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions" \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{"name": "default", "start": true}'
```

---

## Endpoint API — Kirim Pesan

Semua endpoint membutuhkan header `X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf`

### Kirim Text

```bash
curl -X POST https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sendText \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "62812xxxxxxxx@c.us",
    "text": "Halo! Ini balasan dari Satu Cakrawala Bot."
  }'
```

**Response:**
```json
{
  "id": "true_62812xxxxxxxx@c.us_3EB0xxxxxxxxx",
  "timestamp": 1781106328,
  "fromMe": true,
  "chatId": "62812xxxxxxxx@c.us",
  "text": "Halo! Ini balasan dari Satu Cakrawala Bot."
}
```

### Kirim Gambar

```bash
curl -X POST https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sendImage \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "62812xxxxxxxx@c.us",
    "file": {"url": "https://example.com/image.jpg"},
    "caption": "Gambar dari Satu Cakrawala"
  }'
```

### Kirim File

```bash
curl -X POST https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sendFile \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "62812xxxxxxxx@c.us",
    "file": {"url": "https://example.com/document.pdf"},
    "filename": "jadwal-kuliah.pdf"
  }'
```

### Kirim Read/Seen

```bash
curl -X POST https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sendSeen \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "62812xxxxxxxx@c.us"
  }'
```

### Format ChatId

| Tipe | Format | Contoh |
|------|--------|--------|
| Personal | `{nomor}@c.us` | `6281234567890@c.us` |
| Group | `{id_group}@g.us` | `6281234567890-1234567890@g.us` |

> Nomor harus format internasional tanpa `+`, `0`, atau spasi.  
> Contoh: `081234567890` → `6281234567890`

---

## Webhook — Pesan Masuk ke Backend

### Konfigurasi Webhook

Webhook bisa diset **per-session** via API (direkomendasikan):

```bash
# Set webhook saat create session
curl -X POST https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sessions \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "default",
    "start": true,
    "config": {
      "webhooks": [
        {
          "url": "https://api.satucakrawala.ac.id/webhooks/waha",
          "events": ["message", "message.any", "session.status"]
        }
      ]
    }
  }'
```

Atau **global** via env var di `.env`:
```
WHATSAPP_HOOK_URL=https://api.satucakrawala.ac.id/webhooks/waha
WHATSAPP_HOOK_EVENTS=message,message.any,session.status
```

### Event: Pesan Masuk (`message`)

WAHA akan POST ke `https://api.satucakrawala.ac.id/webhooks/waha`:

```json
{
  "id": "evt_01kts3bdntrhmtww9v5dn5hv1j",
  "timestamp": 1781106325178,
  "event": "message",
  "session": "default",
  "me": {
    "id": "62812xxxxxxx@c.us",
    "name": "Satu Cakrawala Bot"
  },
  "payload": {
    "id": "false_62812xxxxxxxx@c.us_3EB0xxxxxxxxx",
    "timestamp": 1781106325,
    "fromMe": false,
    "from": "62812xxxxxxxx@c.us",
    "chatId": "62812xxxxxxxx@c.us",
    "chatName": "Mahasiswa",
    "body": "Halo bot, jadwal hari ini apa?",
    "type": "text",
    "message": {
      "conversation": "Halo bot, jadwal hari ini apa?"
    }
  },
  "engine": "WEBJS",
  "environment": {
    "version": "2026.5.1",
    "engine": "WEBJS",
    "tier": "CORE"
  }
}
```

### Event: Session Status (`session.status`)

```json
{
  "id": "evt_01kts3bh3zwgw9h1wfm1jfcfk0",
  "timestamp": 1781106328703,
  "event": "session.status",
  "session": "default",
  "payload": {
    "name": "default",
    "status": "SCAN_QR_CODE",
    "statuses": [
      {"status": "STARTING", "timestamp": 1781106325178},
      {"status": "SCAN_QR_CODE", "timestamp": 1781106328703}
    ]
  }
}
```

### Field Penting di Webhook Payload

| Field | Deskripsi |
|-------|-----------|
| `event` | Jenis event: `message`, `message.any`, `session.status` |
| `session` | Nama session (selalu `default` di Core) |
| `payload.from` | Nomor pengirim (chatId format) |
| `payload.chatId` | ID chat / group |
| `payload.body` | Isi pesan (text) |
| `payload.id` | Message ID unik |
| `payload.timestamp` | Unix timestamp |
| `payload.type` | Tipe pesan: `text`, `image`, `document`, dll |
| `me.id` | Nomor bot |

### Backend Handler (Contoh)

```python
# Contoh handler di backend Satu Cakrawala
@app.post("/webhooks/waha")
async def handle_waha_webhook(payload: dict):
    event = payload.get("event")
    
    if event == "message":
        from_number = payload["payload"]["from"]
        message_text = payload["payload"]["body"]
        chat_id = payload["payload"]["chatId"]
        message_id = payload["payload"]["id"]
        timestamp = payload["payload"]["timestamp"]
        
        # Process ke AI Agent
        response = await process_message(
            phone=from_number,
            text=message_text,
            chat_id=chat_id
        )
        
        # Kirim balasan via WAHA
        await send_whatsapp_message(chat_id, response)
    
    elif event == "session.status":
        status = payload["payload"]["status"]
        # Log atau alert kalau session disconnect
        logger.info(f"Session status: {status}")
    
    return {"ok": True}


async def send_whatsapp_message(chat_id: str, text: str):
    """Kirim balasan ke WhatsApp via WAHA API"""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://capacity-undertaken-flash-recommendation.trycloudflare.com/api/sendText",
            headers={"X-Api-Key": "4c94510d4aaf48bbb286aaeb65a0bcdf"},
            json={
                "session": "default",
                "chatId": chat_id,
                "text": text
            }
        )
```

---

## Cloudflare Tunnel

### Quick Tunnel (Staging)

```bash
# Start tunnel
cd /home/mannn/satu-cakrawala/waha-gateway
nohup ./cloudflared tunnel --url http://localhost:3001 > tunnel.log 2>&1 &

# Cek URL tunnel
grep "trycloudflare.com" tunnel.log

# Stop tunnel
pkill -f "cloudflared tunnel"
```

> ⚠️ URL berubah setiap kali tunnel di-restart.  
> Untuk Named Tunnel (permanen), setup via dashboard Cloudflare.

---

## Troubleshooting

### WhatsApp Logout / DISCONNECTED

```bash
# Restart session
curl -X POST http://localhost:3001/api/sessions/default/stop \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf"

# Delete dan buat ulang
curl -X DELETE http://localhost:3001/api/sessions/default \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf"

curl -X POST http://localhost:3001/api/sessions \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -H "Content-Type: application/json" \
  -d '{"name":"default","start":true}'

# Scan QR baru
curl -X GET "http://localhost:3001/api/default/auth/qr" \
  -H "X-Api-Key: 4c94510d4aaf48bbb286aaeb65a0bcdf" \
  -o qr-code.png
```

### Container Tidak Healthy

```bash
# Cek logs
docker compose logs --tail 50

# Restart container
docker compose restart

# Kalau masih gagal, recreate
docker compose down && docker compose up -d
```

### Tunnel Mati

```bash
# Cek proses
ps aux | grep cloudflared

# Restart tunnel
cd /home/mannn/satu-cakrawala/waha-gateway
pkill -f "cloudflared tunnel"
nohup ./cloudflared tunnel --url http://localhost:3001 > tunnel.log 2>&1 &

# Cek URL baru
grep "trycloudflare.com" tunnel.log
```

---

## File & Directory

```
/home/mannn/satu-cakrawala/waha-gateway/
├── docker-compose.yml        # Docker config
├── .env                      # Environment variables
├── cloudflared               # Cloudflare Tunnel binary
├── cloudflared-tunnel.service # systemd service file (opsional)
├── .sessions/                # Session data WhatsApp (persist)
├── .media/                   # Media files (persist)
└── README.md                 # Dokumentasi ini
```

---

## Catatan

- **WAHA Core** (gratis) hanya support 1 session bernama `default`
- **Engine**: NOWEB (lightweight, tanpa browser)
- **Session persist** ke disk via `WAHA_SESSION_STORE_TYPE=FILE`
- Quick Tunnel URL bersifat **temporary** — untuk production gunakan Named Tunnel
- Backend AI (Agent, RAG, MCP, dll) **bukan scope WAHA** — WAHA hanya transport
