const express = require('express');
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
const nodemailer = require('nodemailer');
const { OAuth2Client } = require('google-auth-library');

const { promisifyDbGet, promisifyDbRun, promisifyDbAll } = require('../db');
const { generateToken } = require('../middleware/auth');

const googleClient = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

const router = express.Router();

const SALT_ROUNDS = 10;

function createTransporter() {
  const host = process.env.EMAIL_HOST || 'smtp.gmail.com';
  const port = parseInt(process.env.EMAIL_PORT || '587');
  // For port 587, secure should be false (it uses STARTTLS). For 465, secure should be true.
  const secure = port === 465;
  
  return nodemailer.createTransport({
    host,
    port,
    secure: process.env.EMAIL_USE_TLS === 'true' ? false : secure,
    auth: {
      user: process.env.EMAIL_HOST_USER,
      pass: process.env.EMAIL_HOST_PASSWORD
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

async function sendResetEmail(email, resetLink, firstName) {
  console.log('\n' + '='.repeat(60));
  console.log('🔑 [DEVELOPMENT] PASSWORD RESET LINK');
  console.log(`📧 TO: ${email}`);
  console.log(`🔗 LINK: ${resetLink}`);
  console.log('='.repeat(60) + '\n');
  const emailUser = process.env.EMAIL_HOST_USER;
  if (!emailUser) {
    console.error('ERROR: EMAIL_HOST_USER not configured');
    // In dev, we can still proceed if the link is logged
    return process.env.NODE_ENV !== 'production';
  }
  const subject = 'Reset Your HealthTrack+ Password';
  const text = `Hi ${firstName || 'there'},\n\nClick the link below to reset your password. This link expires in 1 hour.\n\n${resetLink}\n\nIf you did not request a password reset, ignore this email.\n\nHealthTrack+ Team`;
  const html = `<div style="font-family:sans-serif;max-width:480px;margin:auto">
    <h2 style="color:#0d9488">Reset Your Password</h2>
    <p>Hi ${firstName || 'there'},</p>
    <p>Click the button below to reset your HealthTrack+ password. This link expires in <strong>1 hour</strong>.</p>
    <a href="${resetLink}" style="display:inline-block;margin:16px 0;padding:12px 24px;background:#0d9488;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold">Reset Password</a>
    <p style="color:#64748b;font-size:12px">If the button doesn't work, copy this link:<br/><a href="${resetLink}">${resetLink}</a></p>
    <p style="color:#64748b;font-size:12px">If you didn't request this, ignore this email.</p>
  </div>`;
  try {
    const transporter = createTransporter();
    await transporter.sendMail({ from: `"HealthTrack+ (No-Reply)" <${emailUser}>`, to: email, subject, text, html });
    console.log(`Reset email sent to ${email}`);
    return true;
  } catch (e) {
    console.error('Error sending reset email:', e.message);
    // Allow local development to proceed if email fails but link is logged
    return process.env.NODE_ENV !== 'production';
  }
}

// Legacy Firebase helpers removed as we use custom auth now.

async function sendVerificationLinkEmail(email, verificationLink, firstName) {
  console.log('\n' + '='.repeat(60));
  console.log('🚀 [DEVELOPMENT] EMAIL VERIFICATION LINK');
  console.log(`📧 TO: ${email}`);
  console.log(`🔗 LINK: ${verificationLink}`);
  console.log('='.repeat(60) + '\n');
  const emailUser = process.env.EMAIL_HOST_USER;
  if (!emailUser) {
    console.error('ERROR: EMAIL_HOST_USER not configured');
    return false;
  }
  const subject = 'Verify Your HealthTrack+ Email';
  const text = `Hi ${firstName || 'there'},\n\nClick the link below to verify your email and complete your registration. This link expires in 10 minutes.\n\n${verificationLink}\n\nIf you did not create an account, ignore this email.\n\nHealthTrack+ Team`;
  const html = `<div style="font-family:sans-serif;max-width:480px;margin:auto">
    <h2 style="color:#0d9488">Verify Your Email</h2>
    <p>Hi ${firstName || 'there'},</p>
    <p>Click the button below to verify your email and activate your HealthTrack+ account. This link expires in <strong>10 minutes</strong>.</p>
    <a href="${verificationLink}" style="display:inline-block;margin:16px 0;padding:12px 24px;background:#0d9488;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold">Verify Email</a>
    <p style="color:#64748b;font-size:12px">If the button doesn't work, copy this link:<br/><a href="${verificationLink}">${verificationLink}</a></p>
    <p style="color:#64748b;font-size:12px">If you didn't create an account, ignore this email.</p>
  </div>`;
  try {
    const transporter = createTransporter();
    await transporter.sendMail({ from: `"HealthTrack+ (No-Reply)" <${emailUser}>`, to: email, subject, text, html });
    console.log(`Verification email sent to ${email}`);
    return true;
  } catch (e) {
    console.error('Error sending verification email:', e.message);
    // Allow local development to proceed if email fails but link is logged
    return process.env.NODE_ENV !== 'production';
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

    if (user.is_email_verified === 0) {
      return res.status(403).json({ 
        success: false, 
        error: 'Email not verified', 
        email: user.email,
        requires_verification: true 
      });
    }

    const token = generateToken(user);

    let userRole = 'patient';
    if (user.is_superuser === 1 || user.user_type === 'admin') userRole = 'admin';
    else if (user.user_type === 'provider' || user.user_type === 'doctor') {
      const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
      if (user.user_type === 'doctor' || (provider && provider.provider_type === 'doctor')) userRole = 'doctor';
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

    const normalizedEmail = email.toLowerCase();
    const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS);
    
    // Determine user type and approval status
    const userType = ['doctor', 'provider'].includes(role) ? 'provider' : 'patient';
    const isApproved = role === 'patient' ? 1 : 0;

    // Create user in DB with is_email_verified = 0
    const result = await promisifyDbRun(
      `INSERT INTO users (username, email, password, first_name, last_name, user_type, is_approved, is_email_verified, city)
       VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)`,
      [username, normalizedEmail, hashedPassword, first_name || '', last_name || '', userType, isApproved, state || '']
    );

    const userId = result.id;

    // If doctor/provider, create service provider record (initially inactive/unverified)
    if (['doctor', 'provider'].includes(role)) {
      await promisifyDbRun(
        `INSERT INTO service_providers (user_id, provider_type, business_name, license_number, specialization, city)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [userId, provider_type || (role === 'doctor' ? 'doctor' : 'pharmacy'), business_name || `${first_name} ${last_name}`, license_number || '', specialization || '', state || '']
      );
    }

    const origin = req.get('origin');
    const forwardedProto = (req.headers['x-forwarded-proto'] || '').toString();
    const forwardedHost = (req.headers['x-forwarded-host'] || '').toString();
    const inferredUrl = forwardedProto && forwardedHost ? `${forwardedProto}://${forwardedHost}` : null;
    const frontendUrl =
      process.env.FRONTEND_URL ||
      origin ||
      inferredUrl ||
      'https://healthtrack.store';

    const otp = generateOtp();
    const expiresAt = new Date(Date.now() + 10 * 60 * 1000).toISOString();
    await promisifyDbRun(
      'INSERT INTO otps (email, otp_code, otp_type, expires_at) VALUES (?, ?, ?, ?)',
      [normalizedEmail, otp, 'register', expiresAt]
    );

    const verificationLink = `${frontendUrl}/verify-email?otp=${otp}&email=${encodeURIComponent(normalizedEmail)}`;
    const emailSent = await sendVerificationLinkEmail(normalizedEmail, verificationLink, first_name);
    
    if (!emailSent) {
      // We still return success because the user IS created, but warn about email
      return res.json({ 
        success: true, 
        email: normalizedEmail, 
        username, 
        message: 'Account created but failed to send verification email. Please try resending from login page.' 
      });
    }

    res.json({ success: true, email: normalizedEmail, username, message: 'Please check your email for the verification link' });
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
      user = await promisifyDbGet('SELECT * FROM users WHERE email = ?', [email]);
      if (!user) {
        return res.status(400).json({ success: false, error: 'User not found' });
      }

      // Mark email as verified
      await promisifyDbRun('UPDATE users SET is_email_verified = 1 WHERE id = ?', [user.id]);
      
      // Update local user object
      user.is_email_verified = 1;
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
    else if (user.user_type === 'provider' || user.user_type === 'doctor') {
      const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
      if (user.user_type === 'doctor' || (provider && provider.provider_type === 'doctor')) userRole = 'doctor';
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
      // Don't reveal whether email exists
      return res.json({ success: true });
    }

    const normalizedEmail = email.toLowerCase();
    const origin = req.get('origin');
    const forwardedProto = (req.headers['x-forwarded-proto'] || '').toString();
    const forwardedHost = (req.headers['x-forwarded-host'] || '').toString();
    const inferredUrl = forwardedProto && forwardedHost ? `${forwardedProto}://${forwardedHost}` : null;
    const frontendUrl =
      process.env.FRONTEND_URL ||
      origin ||
      inferredUrl ||
      'https://healthtrack.store';
    console.log('Forgot-password frontendUrl:', frontendUrl);

    const otp = generateOtp();
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000).toISOString();
    await promisifyDbRun(
      'INSERT INTO otps (email, otp_code, otp_type, expires_at) VALUES (?, ?, ?, ?)',
      [normalizedEmail, otp, 'password_reset', expiresAt]
    );

    const resetLink = `${frontendUrl}/reset-password?otp=${otp}&email=${encodeURIComponent(normalizedEmail)}`;
    const emailSent = await sendResetEmail(normalizedEmail, resetLink, user.first_name);
    
    if (!emailSent) {
      return res.status(500).json({ success: false, error: 'Failed to send reset email. Please check server configuration.' });
    }

    res.json({ success: true });
  } catch (e) {
    console.error('Forgot password error:', e.message);
    res.status(500).json({ success: false, error: 'Failed to send reset email' });
  }
});

router.post('/reset-password', async (req, res) => {
  try {
    const { email, otp, new_password } = req.body;
    if (!email || !otp || !new_password) {
      return res.status(400).json({ success: false, error: 'Email, reset code, and new password are required' });
    }

    const normalizedEmail = email.toLowerCase();
    const otpRecord = await promisifyDbGet(
      'SELECT * FROM otps WHERE email = ? AND otp_code = ? AND otp_type = ? AND expires_at > ? ORDER BY created_at DESC LIMIT 1',
      [normalizedEmail, otp, 'password_reset', new Date().toISOString()]
    );

    if (!otpRecord) {
      return res.status(400).json({ success: false, error: 'Invalid or expired reset link. Please request a new one.' });
    }

    const user = await promisifyDbGet('SELECT * FROM users WHERE email = ?', [normalizedEmail]);
    if (!user) {
      return res.status(404).json({ success: false, error: 'User not found' });
    }

    const hashedPassword = await bcrypt.hash(new_password, SALT_ROUNDS);
    await promisifyDbRun('UPDATE users SET password = ? WHERE id = ?', [hashedPassword, user.id]);

    await promisifyDbRun('DELETE FROM otps WHERE id = ?', [otpRecord.id]);

    res.json({ success: true, message: 'Password updated successfully' });
  } catch (e) {
    console.error('Reset password error:', e.message);
    res.status(400).json({ success: false, error: e.message });
  }
});

router.post('/google-login', async (req, res) => {
  try {
    const { credential, role } = req.body;
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

      const requestedRole = role || 'patient';
      const userType = ['doctor', 'provider'].includes(requestedRole) ? 'provider' : 'patient';
      const isApproved = requestedRole === 'patient' ? 1 : 0;

      const result = await promisifyDbRun(
        `INSERT INTO users (username, email, password, first_name, last_name, user_type, is_approved, is_email_verified, profile_image)
         VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)`,
        [username, email, hashedPassword, given_name || '', family_name || '', userType, isApproved, picture || '']
      );
      user = await promisifyDbGet('SELECT * FROM users WHERE id = ?', [result.id]);

      if (['doctor', 'provider'].includes(requestedRole)) {
        const providerType = requestedRole === 'doctor' ? 'doctor' : 'pharmacy';
        await promisifyDbRun(
          `INSERT INTO service_providers (user_id, provider_type, business_name) VALUES (?, ?, ?)`,
          [user.id, providerType, given_name || username]
        );
      }
    }

    const token = generateToken(user);

    let userRole = 'patient';
    if (user.is_superuser === 1 || user.user_type === 'admin') userRole = 'admin';
    else if (user.user_type === 'provider' || user.user_type === 'doctor') {
      const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
      if (user.user_type === 'doctor' || (provider && provider.provider_type === 'doctor')) userRole = 'doctor';
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


module.exports = router;
