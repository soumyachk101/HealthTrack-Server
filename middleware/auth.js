const jwt = require('jsonwebtoken');
const { promisifyDbGet } = require('../db');

const JWT_SECRET = process.env.JWT_SECRET || 'default-jwt-secret-change-me';
const JWT_ALGORITHM = 'HS256';

function generateToken(user) {
  return jwt.sign(
    {
      user_id: user.id,
      username: user.username,
      email: user.email,
    },
    JWT_SECRET,
    { algorithm: JWT_ALGORITHM, expiresIn: '7d' }
  );
}

async function jwtRequired(req, res, next) {
  const authHeader = req.headers.authorization || '';
  if (!authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Authorization header missing or invalid' });
  }

  const token = authHeader.split(' ', 2)[1];
  try {
    const payload = jwt.verify(token, JWT_SECRET, { algorithms: [JWT_ALGORITHM] });
    const user = await promisifyDbGet('SELECT * FROM users WHERE id = ?', [payload.user_id]);
    if (!user) {
      return res.status(401).json({ error: 'User not found' });
    }
    req.user = user;
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token has expired' });
    }
    return res.status(401).json({ error: 'Invalid token' });
  }
}

async function adminRequired(req, res, next) {
  await jwtRequired(req, res, async () => {
    const isAdmin = req.user.user_type === 'admin' || req.user.is_superuser === 1;
    if (!isAdmin) {
      return res.status(403).json({ success: false, error: 'Admin access required' });
    }
    next();
  });
}

module.exports = { generateToken, jwtRequired, adminRequired };
