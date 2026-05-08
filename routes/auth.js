const express = require('express');
const bcrypt = require('bcryptjs');
const nodemailer = require('nodemailer');
const { OAuth2Client } = require('google-auth-library');
const { firebaseAuth } = require('../firebase');
const { promisifyDbGet, promisifyDbRun, promisifyDbAll } = require('../db');
const { generateToken } = require('../middleware/auth');

const googleClient = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

const router = express.Router();

const SALT_ROUNDS = 10;

function createTransporter() {
  return nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.EMAIL_HOST_USER || '',
      pass: process.env.EMAIL_HOST_PASSWORD || ''
    }
  });
}

function generateOtp() {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

async function sendOtpEmail(email, otp, firstName) {
  const emailUser = process.env.EMAIL_HOST_USER;
  if (!emailUser) {
    console.error('ERROR: EMAIL_HOST_USER is not configured!');
    return false;
  }
  const fromEmail = `"HealthTrack+ (No-Reply)" <${emailUser}>`;

  console.log(`--- [DEVELOPMENT ONLY] OTP for ${email}: ${otp} ---`);

  const subject = 'Your HealthTrack+ Verification Code';
  const text = `Hi ${firstName || 'there'},\n\nYour verification code for HealthTrack+ is:\n\n    ${otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this code, please ignore this email.\n\nBest regards,\nThe HealthTrack+ Team`;

  try {
    const transporter = createTransporter();
    await transporter.sendMail({ from: fromEmail, to: email, subject, text });
    console.log(`Email sent successfully to ${email}`);
    return true;
  } catch (e) {
    console.error('Error sending OTP email:', e.message);
    return false;
  }
}

// Store pending registration in memory (use Redis/DB in production)
const pendingRegistrations = new Map();

router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    const user = await promisifyDbGet('SELECT * FROM users WHERE username = ? OR email = ?', [username, username]);
    if (!user) {
      return res.status(401).json({ success: false, error: 'Invalid credentials' });
    }
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      return res.status(401).json({ success: false, error: 'Invalid credentials' });
    }

    const token = generateToken(user);

    let userRole = 'patient';
    if (user.is_superuser === 1 || user.user_type === 'admin') userRole = 'admin';
    else if (user.user_type === 'provider') {
      const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
      if (provider && provider.provider_type === 'doctor') userRole = 'doctor';
      else userRole = 'provider';
    }

    res.json({
      success: true,
      token,
      user: { id: user.id, username: user.username, email: user.email, role: userRole }
    });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

router.post('/register', async (req, res) => {
  try {
    const { username, email, password, first_name, last_name, role, provider_type, business_name, license_number, specialization, state } = req.body;

    const existingUser = await promisifyDbGet('SELECT * FROM users WHERE username = ? OR email = ?', [username, email]);
    if (existingUser) {
      return res.status(400).json({ success: false, error: 'Username or email already exists' });
    }

    // Store pending registration - Firebase email link will handle verification
    pendingRegistrations.set(email, { username, email, password, first_name, last_name, role, provider_type, business_name, license_number, specialization, state });

    res.json({ success: true, otp_required: true, email, username, message: 'Please verify your email to complete registration' });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

router.post('/verify-otp', async (req, res) => {
  try {
    const { otp, email, otp_type, username } = req.body;
    const now = new Date().toISOString();

    const otpRecord = await promisifyDbGet(
      'SELECT * FROM otps WHERE email = ? AND otp_code = ? AND otp_type = ? AND is_used = 0 AND expires_at > ? ORDER BY id DESC LIMIT 1',
      [email.toLowerCase(), otp, otp_type || 'register', now]
    );

    if (!otpRecord) {
      return res.status(400).json({ success: false, error: 'Invalid or expired OTP' });
    }

    await promisifyDbRun('UPDATE otps SET is_used = 1 WHERE id = ?', [otpRecord.id]);

    let user;
    if (otp_type === 'register' || otp_type === 'password_reset') {
      const regData = pendingRegistrations.get(email);
      if (!regData) {
        return res.status(400).json({ success: false, error: 'Registration session expired' });
      }
      pendingRegistrations.delete(email);

      const hashedPassword = await bcrypt.hash(regData.password, SALT_ROUNDS);
      const role = regData.role || 'patient';
      const userType = ['doctor', 'provider'].includes(role) ? 'provider' : 'patient';
      const isApproved = role === 'patient' ? 1 : 0;

      const result = await promisifyDbRun(
        `INSERT INTO users (username, email, password, first_name, last_name, user_type, is_approved, is_email_verified, city)
         VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)`,
        [regData.username, regData.email, hashedPassword, regData.first_name || '', regData.last_name || '', userType, isApproved, regData.state || '']
      );

      user = await promisifyDbGet('SELECT * FROM users WHERE id = ?', [result.id]);

      if (['doctor', 'provider'].includes(role)) {
        await promisifyDbRun(
          `INSERT INTO service_providers (user_id, provider_type, business_name, license_number, specialization, city)
           VALUES (?, ?, ?, ?, ?, ?)`,
          [user.id, regData.provider_type || (role === 'doctor' ? 'doctor' : 'pharmacy'), regData.business_name || `${user.first_name} ${user.last_name}`, regData.license_number || regData.registration_number || '', regData.specialization || '', regData.state || '']
        );
      }
    } else {
      // login
      const lookup = username || email;
      user = await promisifyDbGet('SELECT * FROM users WHERE username = ? OR email = ?', [lookup, email]);
    }

    if (!user) {
      return res.status(400).json({ success: false, error: 'User not found' });
    }

    const token = generateToken(user);

    let userRole = 'patient';
    if (user.is_superuser === 1 || user.user_type === 'admin') userRole = 'admin';
    else if (user.user_type === 'provider') {
      const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
      if (provider && provider.provider_type === 'doctor') userRole = 'doctor';
      else userRole = 'provider';
    }

    res.json({
      success: true,
      token,
      user: { id: user.id, username: user.username, email: user.email, role: userRole }
    });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

router.post('/resend-otp', async (req, res) => {
  try {
    const { otp_type, email, first_name } = req.body;
    if (!email) {
      return res.status(400).json({ success: false, error: 'Email is required to resend OTP.' });
    }

    const otp = generateOtp();
    const expiresAt = new Date(Date.now() + 10 * 60 * 1000).toISOString();
    await promisifyDbRun(
      'INSERT INTO otps (email, otp_code, otp_type, expires_at) VALUES (?, ?, ?, ?)',
      [email, otp, otp_type || 'register', expiresAt]
    );
    await sendOtpEmail(email, otp, first_name);

    res.json({ success: true, message: 'A new verification code has been sent to your email' });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

router.post('/forgot-password', async (req, res) => {
  try {
    const { email } = req.body;
    if (!email) {
      return res.status(400).json({ success: false, error: 'Email is required' });
    }

    const user = await promisifyDbGet('SELECT * FROM users WHERE email = ?', [email.toLowerCase()]);
    if (!user) {
      return res.json({ success: true });
    }

    try {
      await firebaseAuth.getUserByEmail(email.toLowerCase());
    } catch (fbErr) {
      if (fbErr.code === 'auth/user-not-found') {
        await firebaseAuth.createUser({
          email: email.toLowerCase(),
          displayName: user.first_name ? `${user.first_name} ${user.last_name}`.trim() : user.username,
          emailVerified: true
        });
      }
    }

    res.json({ success: true });
  } catch (e) {
    console.error('Forgot password error:', e.message);
    res.json({ success: true });
  }
});

router.post('/update-password', async (req, res) => {
  try {
    const { email, new_password } = req.body;
    if (!email || !new_password) {
      return res.status(400).json({ success: false, error: 'Email and new password are required' });
    }

    const user = await promisifyDbGet('SELECT * FROM users WHERE email = ?', [email.toLowerCase()]);
    if (!user) {
      return res.status(404).json({ success: false, error: 'User not found' });
    }

    const hashedPassword = await bcrypt.hash(new_password, SALT_ROUNDS);
    await promisifyDbRun('UPDATE users SET password = ? WHERE id = ?', [hashedPassword, user.id]);

    res.json({ success: true, message: 'Password updated successfully' });
  } catch (e) {
    console.error('Update password error:', e.message);
    res.status(400).json({ success: false, error: e.message });
  }
});

router.post('/google-login', async (req, res) => {
  try {
    const { credential } = req.body;
    if (!credential) {
      return res.status(400).json({ success: false, error: 'Google credential is required' });
    }

    const ticket = await googleClient.verifyIdToken({
      idToken: credential,
      audience: process.env.GOOGLE_CLIENT_ID
    });
    const payload = ticket.getPayload();
    const { email, given_name, family_name, picture, sub: googleId } = payload;

    let user = await promisifyDbGet('SELECT * FROM users WHERE email = ?', [email]);

    if (!user) {
      const username = email.split('@')[0] + '_' + googleId.slice(-4);
      const randomPassword = require('crypto').randomBytes(32).toString('hex');
      const hashedPassword = await bcrypt.hash(randomPassword, SALT_ROUNDS);

      const result = await promisifyDbRun(
        `INSERT INTO users (username, email, password, first_name, last_name, user_type, is_approved, is_email_verified, profile_image)
         VALUES (?, ?, ?, ?, ?, 'patient', 1, 1, ?)`,
        [username, email, hashedPassword, given_name || '', family_name || '', picture || '']
      );
      user = await promisifyDbGet('SELECT * FROM users WHERE id = ?', [result.id]);
    }

    const token = generateToken(user);

    let userRole = 'patient';
    if (user.is_superuser === 1 || user.user_type === 'admin') userRole = 'admin';
    else if (user.user_type === 'provider') {
      const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
      if (provider && provider.provider_type === 'doctor') userRole = 'doctor';
      else userRole = 'provider';
    }

    res.json({
      success: true,
      token,
      user: { id: user.id, username: user.username, email: user.email, role: userRole }
    });
  } catch (e) {
    console.error('Google login error:', e.message);
    res.status(400).json({ success: false, error: 'Google authentication failed' });
  }
});

router.post('/verify-email-link', async (req, res) => {
  try {
    const { firebase_token, email, username, otp_type, supabase_verified } = req.body;

    let verifiedEmail = email;

    if (supabase_verified) {
      verifiedEmail = email;
    } else if (firebase_token) {
      const decodedToken = await firebaseAuth.verifyIdToken(firebase_token);
      verifiedEmail = decodedToken.email || email;
    } else {
      return res.status(400).json({ success: false, error: 'Verification token is required' });
    }

    if (otp_type === 'register') {
      const regData = pendingRegistrations.get(verifiedEmail) || pendingRegistrations.get(email);
      if (!regData) {
        return res.status(400).json({ success: false, error: 'Registration data expired. Please register again.' });
      }

      const hashedPassword = await bcrypt.hash(regData.password, SALT_ROUNDS);
      const result = await promisifyDbRun(
        `INSERT INTO users (username, email, password, first_name, last_name, user_type, is_approved, is_email_verified)
         VALUES (?, ?, ?, ?, ?, ?, ?, 1)`,
        [regData.username, verifiedEmail, hashedPassword, regData.first_name || '', regData.last_name || '', regData.role || 'patient', regData.role === 'patient' ? 1 : 0]
      );

      const user = await promisifyDbGet('SELECT * FROM users WHERE id = ?', [result.id]);
      pendingRegistrations.delete(verifiedEmail);
      pendingRegistrations.delete(email);

      if (regData.role === 'provider' || regData.role === 'doctor') {
        await promisifyDbRun(
          'INSERT INTO service_providers (user_id, provider_type, business_name) VALUES (?, ?, ?)',
          [user.id, regData.role, regData.username]
        );
      }

      const token = generateToken(user);
      let userRole = user.user_type || 'patient';
      if (user.is_superuser === 1) userRole = 'admin';

      return res.json({
        success: true,
        token,
        user: { id: user.id, username: user.username, email: user.email, role: userRole }
      });
    }

    // Login verification
    const user = await promisifyDbGet('SELECT * FROM users WHERE email = ?', [verifiedEmail]);
    if (!user) {
      return res.status(400).json({ success: false, error: 'User not found' });
    }

    const token = generateToken(user);
    let userRole = 'patient';
    if (user.is_superuser === 1 || user.user_type === 'admin') userRole = 'admin';
    else if (user.user_type === 'provider') {
      const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
      if (provider && provider.provider_type === 'doctor') userRole = 'doctor';
      else userRole = 'provider';
    }

    res.json({
      success: true,
      token,
      user: { id: user.id, username: user.username, email: user.email, role: userRole }
    });
  } catch (e) {
    console.error('Email link verification error:', e.message);
    res.status(400).json({ success: false, error: 'Email verification failed. Link may have expired.' });
  }
});

module.exports = router;
