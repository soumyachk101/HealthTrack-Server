const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 5,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 10000
});

pool.on('connect', () => {
  console.log('Connected to PostgreSQL (Neon).');
});

pool.on('error', (err) => {
  console.error('Unexpected PG pool error:', err);
});

async function initDatabase() {
  const client = await pool.connect();
  try {
    await client.query(`CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      first_name TEXT DEFAULT '',
      last_name TEXT DEFAULT '',
      user_type TEXT DEFAULT 'patient',
      phone TEXT DEFAULT '',
      address TEXT DEFAULT '',
      city TEXT DEFAULT '',
      date_of_birth TEXT,
      profile_image TEXT,
      emergency_contact TEXT DEFAULT '',
      emergency_phone TEXT DEFAULT '',
      blood_group TEXT DEFAULT '',
      is_approved INTEGER DEFAULT 0,
      is_email_verified INTEGER DEFAULT 0,
      verification_token TEXT,
      is_superuser INTEGER DEFAULT 0,
      is_staff INTEGER DEFAULT 0,
      is_active INTEGER DEFAULT 1,
      date_joined TIMESTAMPTZ DEFAULT NOW(),
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS service_providers (
      id SERIAL PRIMARY KEY,
      user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      provider_type TEXT DEFAULT 'doctor',
      business_name TEXT NOT NULL,
      license_number TEXT DEFAULT '',
      specialization TEXT DEFAULT '',
      working_hours TEXT DEFAULT '',
      services_offered TEXT DEFAULT '',
      rating REAL DEFAULT 0.0,
      total_reviews INTEGER DEFAULT 0
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS otps (
      id SERIAL PRIMARY KEY,
      email TEXT NOT NULL,
      otp_code TEXT NOT NULL,
      otp_type TEXT DEFAULT 'register',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      is_used INTEGER DEFAULT 0,
      expires_at TIMESTAMPTZ NOT NULL
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS health_records (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      blood_pressure_systolic INTEGER,
      blood_pressure_diastolic INTEGER,
      blood_sugar REAL,
      weight REAL,
      heart_rate INTEGER,
      temperature REAL,
      oxygen_level INTEGER,
      notes TEXT DEFAULT '',
      recorded_at TIMESTAMPTZ DEFAULT NOW(),
      created_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS medicines (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      dosage TEXT NOT NULL,
      frequency TEXT DEFAULT 'once',
      start_date TEXT NOT NULL,
      end_date TEXT,
      prescribed_by TEXT DEFAULT '',
      notes TEXT DEFAULT '',
      is_active INTEGER DEFAULT 1,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS prescriptions (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      doctor_name TEXT NOT NULL,
      hospital_name TEXT DEFAULT '',
      diagnosis TEXT DEFAULT '',
      prescription_date TEXT NOT NULL,
      follow_up_date TEXT,
      document TEXT,
      notes TEXT DEFAULT '',
      created_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS mental_health_logs (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      mood_score INTEGER DEFAULT 3,
      stress_level INTEGER DEFAULT 3,
      sleep_hours REAL,
      sleep_quality INTEGER,
      anxiety_level INTEGER,
      notes TEXT DEFAULT '',
      recorded_at TIMESTAMPTZ DEFAULT NOW(),
      created_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS insurance_policies (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      policy_type TEXT DEFAULT 'health',
      provider_name TEXT NOT NULL,
      policy_number TEXT NOT NULL,
      coverage_amount REAL NOT NULL,
      premium_amount REAL NOT NULL,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      document TEXT,
      is_active INTEGER DEFAULT 1,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS lifestyle_logs (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      water_intake INTEGER DEFAULT 0,
      exercise_minutes INTEGER DEFAULT 0,
      steps_count INTEGER DEFAULT 0,
      calories_consumed INTEGER,
      calories_burned INTEGER,
      smoking_count INTEGER DEFAULT 0,
      alcohol_units INTEGER DEFAULT 0,
      notes TEXT DEFAULT '',
      recorded_at DATE DEFAULT CURRENT_DATE,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      UNIQUE(user_id, recorded_at)
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS activity_logs (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      action TEXT DEFAULT 'login',
      details TEXT DEFAULT '',
      ip_address TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS system_settings (
      id SERIAL PRIMARY KEY,
      key TEXT UNIQUE NOT NULL,
      value TEXT NOT NULL,
      description TEXT DEFAULT '',
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS appointments (
      id SERIAL PRIMARY KEY,
      patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      date TEXT NOT NULL,
      time TEXT NOT NULL,
      reason TEXT NOT NULL,
      status TEXT DEFAULT 'pending',
      type TEXT DEFAULT 'Video Consult',
      meeting_link TEXT,
      notes TEXT DEFAULT '',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS services (
      id SERIAL PRIMARY KEY,
      provider_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      description TEXT NOT NULL,
      price REAL NOT NULL,
      duration_minutes INTEGER DEFAULT 60,
      is_active INTEGER DEFAULT 1
    )`);

    await client.query(`CREATE TABLE IF NOT EXISTS service_requests (
      id SERIAL PRIMARY KEY,
      patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      provider_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      service_name TEXT NOT NULL,
      service_price REAL NOT NULL,
      address TEXT NOT NULL,
      scheduled_date TEXT,
      items TEXT DEFAULT '',
      status TEXT DEFAULT 'pending',
      notes TEXT DEFAULT '',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )`);

    await client.query(`CREATE INDEX IF NOT EXISTS idx_health_records_user ON health_records(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_medicines_user ON medicines(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_prescriptions_user ON prescriptions(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_otps_email ON otps(email)`);

    console.log('Database tables initialized.');
  } finally {
    client.release();
  }
}

// SQLite-compatible wrapper functions using $1, $2 style params
// Convert ? placeholders to $1, $2, etc.
function convertPlaceholders(sql) {
  let i = 0;
  return sql.replace(/\?/g, () => `$${++i}`);
}

async function promisifyDbRun(sql, params = []) {
  const pgSql = convertPlaceholders(sql);
  const isInsert = sql.trim().toUpperCase().startsWith('INSERT');
  const finalSql = isInsert && !pgSql.toUpperCase().includes('RETURNING') ? pgSql + ' RETURNING *' : pgSql;
  const result = await pool.query(finalSql, params);
  const row = result.rows ? result.rows[0] : null;
  return { id: row ? row.id : null, changes: result.rowCount };
}

async function promisifyDbAll(sql, params = []) {
  const pgSql = convertPlaceholders(sql);
  const result = await pool.query(pgSql, params);
  return result.rows;
}

async function promisifyDbGet(sql, params = []) {
  const pgSql = convertPlaceholders(sql);
  const result = await pool.query(pgSql, params);
  return result.rows[0] || null;
}

// Initialize on first import
initDatabase().catch(err => console.error('DB init error:', err));

module.exports = {
  pool,
  promisifyDbRun,
  promisifyDbAll,
  promisifyDbGet,
  initDatabase
};
