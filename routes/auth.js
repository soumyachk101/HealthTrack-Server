const express = require('express');
const bcrypt = require('bcryptjs');
const nodemailer = require('nodemailer');
const { promisifyDbGet, promisifyDbRun, promisifyDbAll } = require('../db');
const { generateToken } = require('../middleware/auth');

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
  const fromEmail = process.env.EMAIL_HOST_USER || 'noreply@healthtrack.plus';
  if (!fromEmail) {
    console.error('ERROR: EMAIL_HOST_USER is not configured!');
    return false;
  }

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

    // Generate OTP
    const otp = generateOtp();
    const expiresAt = new Date(Date.now() + 10 * 60 * 1000).toISOString();
    await promisifyDbRun(
      'INSERT INTO otps (email, otp_code, otp_type, expires_at) VALUES (?, ?, ?, ?)',
      [user.email, otp, 'login', expiresAt]
    );
    await sendOtpEmail(user.email, otp, user.first_name);

    res.json({ success: true, otp_required: true, email: user.email, username: user.username, message: 'Verification code sent to your email' });
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

    // Store pending registration
    pendingRegistrations.set(email, { username, email, password, first_name, last_name, role, provider_type, business_name, license_number, specialization, state });

    // Generate OTP
    const otp = generateOtp();
    const expiresAt = new Date(Date.now() + 10 * 60 * 1000).toISOString();
    await promisifyDbRun(
      'INSERT INTO otps (email, otp_code, otp_type, expires_at) VALUES (?, ?, ?, ?)',
      [email, otp, 'register', expiresAt]
    );
    await sendOtpEmail(email, otp, first_name);

    res.json({ success: true, otp_required: true, message: 'Verification code sent to your email' });
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

module.exports = router;
