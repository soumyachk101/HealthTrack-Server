const express = require('express');
const { promisifyDbAll, promisifyDbGet, promisifyDbRun } = require('../db');
const { jwtRequired } = require('../middleware/auth');

const router = express.Router();

function getBpStatus(sys, dia) {
  if (!sys || !dia) return 'Unknown';
  if (sys < 120 && dia < 80) return 'Normal';
  if (sys < 130 && dia < 80) return 'Elevated';
  if (sys < 140 || dia < 90) return 'High (Stage 1)';
  return 'High (Stage 2)';
}

function moodDisplay(score) {
  const map = { 1: 'Very Low', 2: 'Low', 3: 'Neutral', 4: 'Good', 5: 'Excellent' };
  return map[score] || 'Unknown';
}

function frequencyDisplay(freq) {
  const map = { once: 'Once Daily', twice: 'Twice Daily', thrice: 'Three Times Daily', asneeded: 'As Needed' };
  return map[freq] || freq;
}

function policyTypeDisplay(pt) {
  const map = { health: 'Health Insurance', life: 'Life Insurance', term: 'Term Life Insurance' };
  return map[pt] || pt;
}

// Dashboard
router.get('/dashboard', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const latestRecord = await promisifyDbGet('SELECT * FROM health_records WHERE user_id = ? ORDER BY recorded_at DESC LIMIT 1', [user.id]);
    let latestRecordData = null;
    if (latestRecord) {
      latestRecordData = {
        blood_pressure_systolic: latestRecord.blood_pressure_systolic,
        blood_pressure_diastolic: latestRecord.blood_pressure_diastolic,
        bp_status: getBpStatus(latestRecord.blood_pressure_systolic, latestRecord.blood_pressure_diastolic),
        blood_sugar: latestRecord.blood_sugar ? String(latestRecord.blood_sugar) : null,
        weight: latestRecord.weight ? String(latestRecord.weight) : null,
        heart_rate: latestRecord.heart_rate,
        recorded_at: latestRecord.recorded_at
      };
    }

    const activeMedicines = await promisifyDbGet('SELECT COUNT(*) as count FROM medicines WHERE user_id = ? AND is_active = 1', [user.id]);
    const recentActivities = await promisifyDbAll('SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', [user.id]);

    const latestMental = await promisifyDbGet('SELECT * FROM mental_health_logs WHERE user_id = ? ORDER BY recorded_at DESC LIMIT 1', [user.id]);
    let mentalData = null;
    if (latestMental) {
      mentalData = {
        sleep_hours: latestMental.sleep_hours ? String(latestMental.sleep_hours) : null,
        mood_score: latestMental.mood_score,
        stress_level: latestMental.stress_level
      };
    }

    res.json({
      user: {
        name: `${user.first_name} ${user.last_name}`.trim() || user.username,
        email: user.email
      },
      latest_record: latestRecordData,
      active_medicines: activeMedicines.count,
      active_medicines_count: activeMedicines.count,
      recent_activities: recentActivities.map(a => ({
        action: a.action,
        action_display: a.action,
        details: a.details,
        created_at: a.created_at,
        created_at_since: a.created_at
      })),
      latest_mental_health: mentalData
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Add health record
router.post('/health-track/add', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const { blood_pressure_systolic, blood_pressure_diastolic, blood_sugar, weight, heart_rate, temperature, oxygen_level, notes } = req.body;
    await promisifyDbRun(
      `INSERT INTO health_records (user_id, blood_pressure_systolic, blood_pressure_diastolic, blood_sugar, weight, heart_rate, temperature, oxygen_level, notes)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [user.id, blood_pressure_systolic || null, blood_pressure_diastolic || null, blood_sugar || null, weight || null, heart_rate || null, temperature || null, oxygen_level || null, notes || '']
    );
    res.json({ message: 'Health record added successfully' });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Add medicine
router.post('/medicines/add', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const { name, dosage, frequency, start_date, end_date, prescribed_by, notes } = req.body;
    await promisifyDbRun(
      `INSERT INTO medicines (user_id, name, dosage, frequency, start_date, end_date, prescribed_by, notes)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [user.id, name, dosage, frequency || 'once', start_date, end_date || null, prescribed_by || '', notes || '']
    );
    res.json({ message: 'Medicine added successfully' });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Add prescription
router.post('/prescriptions/add', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const { doctor_name, hospital_name, diagnosis, prescription_date, follow_up_date, notes } = req.body;
    await promisifyDbRun(
      `INSERT INTO prescriptions (user_id, doctor_name, hospital_name, diagnosis, prescription_date, follow_up_date, notes)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [user.id, doctor_name, hospital_name || '', diagnosis || '', prescription_date || new Date().toISOString().split('T')[0], follow_up_date || null, notes || '']
    );
    res.json({ message: 'Prescription added successfully' });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Get medicines
router.get('/medicines', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const medicines = await promisifyDbAll('SELECT * FROM medicines WHERE user_id = ? ORDER BY created_at DESC', [user.id]);
    const activeCount = await promisifyDbGet('SELECT COUNT(*) as count FROM medicines WHERE user_id = ? AND is_active = 1', [user.id]);
    res.json({
      medicines: medicines.map(m => ({
        name: m.name,
        dosage: m.dosage,
        frequency_display: frequencyDisplay(m.frequency),
        start_date: m.start_date,
        end_date: m.end_date,
        is_active: m.is_active === 1
      })),
      active_count: activeCount.count
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Get health track
router.get('/health-track', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const records = await promisifyDbAll('SELECT * FROM health_records WHERE user_id = ? ORDER BY recorded_at DESC', [user.id]);
    res.json({
      records: records.map(r => ({
        recorded_at: r.recorded_at,
        blood_pressure_systolic: r.blood_pressure_systolic,
        blood_pressure_diastolic: r.blood_pressure_diastolic,
        blood_sugar: r.blood_sugar ? String(r.blood_sugar) : null,
        weight: r.weight ? String(r.weight) : null,
        heart_rate: r.heart_rate,
        oxygen_level: r.oxygen_level ? String(r.oxygen_level) : null,
        bp_status: getBpStatus(r.blood_pressure_systolic, r.blood_pressure_diastolic)
      }))
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Get prescriptions
router.get('/prescriptions', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const prescriptions = await promisifyDbAll('SELECT * FROM prescriptions WHERE user_id = ? ORDER BY created_at DESC', [user.id]);
    res.json({
      prescriptions: prescriptions.map(p => ({
        prescription_date: p.created_at ? p.created_at.split('T')[0] : '',
        doctor_name: p.doctor_name,
        hospital_name: p.hospital_name,
        diagnosis: p.notes && p.notes.length > 50 ? p.notes.slice(0, 50) + '...' : p.notes,
        follow_up_date: p.follow_up_date
      }))
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Profile
router.get('/profile', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const profileData = {
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      phone: user.phone || '',
      city: user.city || '',
      blood_group: user.blood_group || '',
      address: user.address || '',
      emergency_contact: user.emergency_contact || '',
      emergency_phone: user.emergency_phone || ''
    };
    res.json({ user: profileData, messages: [{ tags: 'success', message: `Welcome back, ${user.username}!` }] });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Mental health
router.get('/mental-health', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const logs = await promisifyDbAll('SELECT * FROM mental_health_logs WHERE user_id = ? ORDER BY recorded_at DESC', [user.id]);
    const avgMood = logs.length ? (logs.reduce((sum, l) => sum + l.mood_score, 0) / logs.length).toFixed(1) : 0;
    res.json({
      avg_mood: parseFloat(avgMood),
      logs: logs.map(l => ({
        recorded_at: l.recorded_at,
        mood_score: l.mood_score,
        mood_score_display: moodDisplay(l.mood_score),
        stress_level_display: moodDisplay(l.stress_level),
        sleep_hours: l.sleep_hours ? parseFloat(l.sleep_hours) : null,
        notes: l.notes
      }))
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Lifestyle
router.get('/lifestyle', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const logs = await promisifyDbAll('SELECT * FROM lifestyle_logs WHERE user_id = ? ORDER BY recorded_at DESC', [user.id]);
    res.json({
      logs: logs.map(l => ({
        recorded_at: l.recorded_at,
        water_intake: l.water_intake,
        exercise_minutes: l.exercise_minutes,
        steps_count: l.steps_count,
        calories_consumed: l.calories_consumed
      }))
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Insurance
router.get('/insurance', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const policies = await promisifyDbAll('SELECT * FROM insurance_policies WHERE user_id = ? ORDER BY created_at DESC', [user.id]);
    const activePolicies = await promisifyDbGet('SELECT COUNT(*) as count FROM insurance_policies WHERE user_id = ? AND is_active = 1', [user.id]);
    res.json({
      policies: policies.map(p => ({
        provider_name: p.provider_name,
        policy_type_display: policyTypeDisplay(p.policy_type),
        policy_number: p.policy_number,
        coverage_amount: p.coverage_amount,
        end_date: p.end_date,
        is_active: p.is_active === 1
      })),
      active_policies: activePolicies.count
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Past records
router.get('/past-records', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const healthRecords = await promisifyDbAll('SELECT * FROM health_records WHERE user_id = ? ORDER BY recorded_at DESC', [user.id]);
    const prescriptions = await promisifyDbAll('SELECT * FROM prescriptions WHERE user_id = ? ORDER BY prescription_date DESC', [user.id]);
    res.json({
      health_records: healthRecords.map(r => ({
        recorded_at: r.recorded_at ? r.recorded_at.split('T')[0] : '',
        blood_pressure_systolic: r.blood_pressure_systolic,
        blood_pressure_diastolic: r.blood_pressure_diastolic
      })),
      prescriptions: prescriptions.map(p => ({
        prescription_date: p.prescription_date,
        doctor_name: p.doctor_name
      }))
    });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// Appointments
router.route('/appointments')
  .get(jwtRequired, async (req, res) => {
    try {
      const user = req.user;
      let appointments;
      if (user.user_type === 'provider') {
        const provider = await promisifyDbGet('SELECT * FROM service_providers WHERE user_id = ?', [user.id]);
        if (!provider || provider.provider_type !== 'doctor') {
          return res.status(403).json({ success: false, error: 'Not a doctor' });
        }
        appointments = await promisifyDbAll('SELECT a.*, p.first_name as p_first, p.last_name as p_last, d.first_name as d_first, d.last_name as d_last FROM appointments a JOIN users p ON a.patient_id = p.id JOIN users d ON a.doctor_id = d.id WHERE a.doctor_id = ? ORDER BY a.date, a.time', [user.id]);
      } else {
        appointments = await promisifyDbAll('SELECT a.*, p.first_name as p_first, p.last_name as p_last, d.first_name as d_first, d.last_name as d_last FROM appointments a JOIN users p ON a.patient_id = p.id JOIN users d ON a.doctor_id = d.id WHERE a.patient_id = ? ORDER BY a.date, a.time', [user.id]);
      }
      res.json({
        success: true,
        appointments: appointments.map(a => ({
          id: a.id,
          patient_name: `${a.p_first || ''} ${a.p_last || ''}`.trim(),
          doctor_name: `${a.d_first || ''} ${a.d_last || ''}`.trim(),
          date: a.date,
          time: a.time,
          reason: a.reason,
          status: a.status,
          type: a.type,
          meeting_link: a.meeting_link
        }))
      });
    } catch (e) {
      res.status(400).json({ success: false, error: e.message });
    }
  })
  .post(jwtRequired, async (req, res) => {
    try {
      const user = req.user;
      const { doctor_id, date, time, reason, type } = req.body;
      const result = await promisifyDbRun(
        'INSERT INTO appointments (patient_id, doctor_id, date, time, reason, type) VALUES (?, ?, ?, ?, ?, ?)',
        [user.id, doctor_id, date, time, reason, type || 'Video Consult']
      );
      await promisifyDbRun('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)', [user.id, 'appointment_booked', `Booked appointment with doctor ${doctor_id}`]);
      res.json({ success: true, message: 'Appointment booked successfully', id: result.id });
    } catch (e) {
      res.status(400).json({ success: false, error: e.message });
    }
  });

// Appointment action
router.post('/appointments/:appointment_id/action', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const { action } = req.body;
    const appt = await promisifyDbGet('SELECT * FROM appointments WHERE id = ?', [req.params.appointment_id]);
    if (!appt) return res.status(404).json({ success: false, error: 'Appointment not found' });
    if (appt.doctor_id !== user.id) return res.status(403).json({ success: false, error: 'Permission denied' });

    let status = appt.status;
    let meetingLink = appt.meeting_link;
    if (action === 'accept') {
      status = 'confirmed';
      if (appt.type === 'Video Consult') meetingLink = 'https://meet.google.com/new';
    } else if (action === 'reject') {
      status = 'cancelled';
    } else if (action === 'complete') {
      status = 'completed';
    }

    await promisifyDbRun('UPDATE appointments SET status = ?, meeting_link = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', [status, meetingLink, appt.id]);
    res.json({ success: true, status });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

// Service requests
router.route('/service-requests')
  .get(jwtRequired, async (req, res) => {
    try {
      const user = req.user;
      let requests;
      if (user.user_type === 'provider') {
        requests = await promisifyDbAll('SELECT r.*, p.first_name as p_first, p.last_name as p_last, pv.first_name as pv_first, pv.last_name as pv_last FROM service_requests r JOIN users p ON r.patient_id = p.id JOIN users pv ON r.provider_id = pv.id WHERE r.provider_id = ? ORDER BY r.created_at DESC', [user.id]);
      } else {
        requests = await promisifyDbAll('SELECT r.*, p.first_name as p_first, p.last_name as p_last, pv.first_name as pv_first, pv.last_name as pv_last FROM service_requests r JOIN users p ON r.patient_id = p.id JOIN users pv ON r.provider_id = pv.id WHERE r.patient_id = ? ORDER BY r.created_at DESC', [user.id]);
      }
      res.json({
        success: true,
        requests: requests.map(r => ({
          id: r.id,
          patient_name: `${r.p_first || ''} ${r.p_last || ''}`.trim(),
          provider_name: `${r.pv_first || ''} ${r.pv_last || ''}`.trim(),
          service_name: r.service_name,
          price: r.service_price,
          status: r.status,
          address: r.address,
          scheduled_date: r.scheduled_date
        }))
      });
    } catch (e) {
      res.status(400).json({ success: false, error: e.message });
    }
  })
  .post(jwtRequired, async (req, res) => {
    try {
      const user = req.user;
      const { provider_id, service_name, price, address } = req.body;
      const result = await promisifyDbRun(
        'INSERT INTO service_requests (patient_id, provider_id, service_name, service_price, address) VALUES (?, ?, ?, ?, ?)',
        [user.id, provider_id, service_name, price, address]
      );
      await promisifyDbRun('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)', [user.id, 'service_requested', `Requested ${service_name} from provider ${provider_id}`]);
      res.json({ success: true, message: 'Service requested successfully', id: result.id });
    } catch (e) {
      res.status(400).json({ success: false, error: e.message });
    }
  });

// Service request action
router.post('/service-requests/:request_id/action', jwtRequired, async (req, res) => {
  try {
    const user = req.user;
    const { action } = req.body;
    const reqRecord = await promisifyDbGet('SELECT * FROM service_requests WHERE id = ?', [req.params.request_id]);
    if (!reqRecord) return res.status(404).json({ success: false, error: 'Service request not found' });
    if (reqRecord.provider_id !== user.id) return res.status(403).json({ success: false, error: 'Permission denied' });

    let status = reqRecord.status;
    if (action === 'accept') status = 'accepted';
    else if (action === 'decline') status = 'declined';
    else if (action === 'complete') status = 'completed';

    await promisifyDbRun('UPDATE service_requests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', [status, reqRecord.id]);
    res.json({ success: true, status });
  } catch (e) {
    res.status(400).json({ success: false, error: e.message });
  }
});

module.exports = router;
