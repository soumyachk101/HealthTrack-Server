const express = require('express');
const { promisifyDbAll, promisifyDbGet, promisifyDbRun } = require('../db');
const { adminRequired } = require('../middleware/auth');

const router = express.Router();

router.get('/stats', adminRequired, async (req, res) => {
  try {
    const totalUsers = await promisifyDbGet('SELECT COUNT(*) as count FROM users');
    const patients = await promisifyDbGet("SELECT COUNT(*) as count FROM users WHERE user_type = 'patient'");
    const providers = await promisifyDbGet("SELECT COUNT(*) as count FROM users WHERE user_type = 'provider'");
    const pendingApprovals = await promisifyDbGet("SELECT COUNT(*) as count FROM users WHERE is_approved = 0 AND user_type IN ('provider','doctor')");
    const totalRecords = await promisifyDbGet('SELECT COUNT(*) as count FROM health_records');

    res.json({
      success: true,
      stats: {
        total_users: Number(totalUsers.count),
        patients: Number(patients.count),
        providers: Number(providers.count),
        pending_approvals: Number(pendingApprovals.count),
        total_records: Number(totalRecords.count)
      }
    });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

router.get('/users', adminRequired, async (req, res) => {
  try {
    const { type, search } = req.query;
    let sql = 'SELECT * FROM users ORDER BY created_at DESC';
    let params = [];
    const conditions = [];

    if (type) {
      conditions.push('user_type = ?');
      params.push(type);
    }
    if (search) {
      conditions.push('(email LIKE ? OR username LIKE ?)');
      params.push(`%${search}%`, `%${search}%`);
    }
    if (conditions.length) {
      sql = `SELECT * FROM users WHERE ${conditions.join(' AND ')} ORDER BY created_at DESC`;
    }

    const users = await promisifyDbAll(sql, params);
    const userList = [];
    for (const user of users) {
      let displayRole = user.user_type;
      if (user.user_type === 'provider') {
        const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
        if (provider) displayRole = provider.provider_type;
      }
      const dj = user.date_joined;
      let dateStr = '';
      if (dj instanceof Date) dateStr = dj.toISOString().split('T')[0];
      else if (typeof dj === 'string') dateStr = dj.split('T')[0];

      userList.push({
        id: user.id,
        username: user.username,
        email: user.email,
        user_type: displayRole,
        is_approved: user.is_approved === 1,
        date_joined: dateStr
      });
    }
    res.json({ success: true, users: userList });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

router.post('/users/:user_id/action', adminRequired, async (req, res) => {
  try {
    const { action } = req.body;
    const userId = req.params.user_id;
    const user = await promisifyDbGet('SELECT * FROM users WHERE id = ?', [userId]);
    if (!user) return res.status(404).json({ success: false, error: 'User not found' });

    if (action === 'approve') {
      await promisifyDbRun('UPDATE users SET is_approved = 1 WHERE id = ?', [userId]);
      await promisifyDbRun('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)', [req.user.id, 'admin_action', `Approved user ${user.email}`]);
    } else if (action === 'reject') {
      await promisifyDbRun('UPDATE users SET is_approved = 0 WHERE id = ?', [userId]);
      await promisifyDbRun('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)', [req.user.id, 'admin_action', `Rejected user ${user.email}`]);
    } else if (action === 'delete') {
      await promisifyDbRun('DELETE FROM users WHERE id = ?', [userId]);
      await promisifyDbRun('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)', [req.user.id, 'admin_action', `Deleted user ${user.email}`]);
    }
    res.json({ success: true });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

module.exports = router;
