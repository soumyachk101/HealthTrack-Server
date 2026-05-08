# HealthTrack+ Node.js Backend

This is the Node.js/Express backend for the HealthTrack+ application, converted from the original Django backend.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

3. Start the server:
```bash
npm start
```

For development with auto-reload:
```bash
npm run dev
```

## API Endpoints

### Authentication (`/accounts/api/`)
- `POST /accounts/api/login` - Login with username/password (sends OTP)
- `POST /accounts/api/register` - Register new user (sends OTP)
- `POST /accounts/api/verify-otp` - Verify OTP and get JWT token
- `POST /accounts/api/resend-otp` - Resend OTP

### Core APIs (`/api/`)
- `GET /api/dashboard` - Dashboard data
- `GET /api/health-track` - Health records list
- `POST /api/health-track/add` - Add health record
- `GET /api/medicines` - Medicines list
- `POST /api/medicines/add` - Add medicine
- `GET /api/prescriptions` - Prescriptions list
- `POST /api/prescriptions/add` - Add prescription
- `GET /api/profile` - User profile
- `GET /api/mental-health` - Mental health logs
- `GET /api/lifestyle` - Lifestyle logs
- `GET /api/insurance` - Insurance policies
- `GET /api/past-records` - Past health records & prescriptions
- `GET/POST /api/appointments` - List/create appointments
- `POST /api/appointments/:id/action` - Accept/reject/complete appointment
- `GET/POST /api/service-requests` - List/create service requests
- `POST /api/service-requests/:id/action` - Accept/decline/complete request

### Chatbot (`/chatbot/`)
- `POST /chatbot/api` - AI chat (Groq/OpenRouter)
- `POST /chatbot/api/tts` - Text-to-speech (Sarvam)

### Admin (`/api/`)
- `GET /api/stats` - Admin statistics
- `GET /api/users` - List users (with optional `?type=` and `?search=`)
- `POST /api/users/:id/action` - Approve/reject/delete user

## Tech Stack
- **Runtime:** Node.js
- **Framework:** Express.js
- **Database:** SQLite3
- **Auth:** JWT (jsonwebtoken) + bcryptjs
- **Email:** Nodemailer (SMTP)
- **AI:** Groq / OpenRouter APIs
- **TTS:** Sarvam API
