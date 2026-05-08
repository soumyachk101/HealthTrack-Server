require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
// const { firestore } = require('./firebase'); // Lazy-load when needed

const app = express();
const PORT = process.env.PORT || 8000;

// Strip trailing slashes to match Django URL patterns (frontend sends /api/dashboard/)
app.use((req, res, next) => {
  if (req.path.length > 1 && req.path.endsWith('/')) {
    const newPath = req.path.slice(0, -1);
    const query = req.url.includes('?') ? req.url.slice(req.url.indexOf('?')) : '';
    req.url = newPath + query;
  }
  next();
});

// CORS setup
const corsOrigins = (process.env.CORS_ALLOWED_ORIGINS || 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000').split(',').map(s => s.trim());
app.use(cors({
  origin: function(origin, callback) {
    if (!origin || corsOrigins.includes(origin) || corsOrigins.includes('*') ||
        origin.endsWith('.vercel.app') || origin.endsWith('.netlify.app') ||
        origin.endsWith('.healthtrack.store') || origin === 'https://healthtrack.store') {
      callback(null, true);
    } else {
      callback(null, false);
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Accept', 'Accept-Encoding', 'Authorization', 'Content-Type', 'DNT', 'Origin', 'User-Agent', 'X-Requested-With', 'X-CSRFToken']
}));

// Handle preflight for all routes
app.options('*', cors());

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static uploads
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/', (req, res) => {
  res.json({ message: 'HealthTrack+ API Server is Running' });
});

// Routes
app.use('/accounts/api', require('./routes/auth'));
app.use('/api', require('./routes/core'));
app.use('/chatbot', require('./routes/chatbot'));
app.use('/admin-panel/api', require('./routes/admin'));

// Catch-all
app.get('*', (req, res) => {
  res.json({ message: 'HealthTrack+ API Server' });
});

app.listen(PORT, () => {
  console.log(`HealthTrack+ server running on port ${PORT}`);
});
