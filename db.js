const { Pool } = require('pg');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

let pool;
let isSQLite = false;
let sqliteDb;

// Try to initialize PostgreSQL
if (process.env.DATABASE_URL) {
  pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
    max: 5,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 10000
  });

  pool.on('error', (err) => {
    console.error('Unexpected PG pool error:', err);
  });
}

async function initDatabase() {
  try {
    if (pool) {
      console.log('Attempting to connect to PostgreSQL (Neon)...');
      const client = await pool.connect();
      console.log('✅ Connected to PostgreSQL.');
      await createTables(client, 'pg');
      client.release();
    } else {
      throw new Error('No DATABASE_URL provided');
    }
  } catch (err) {
    console.error('❌ PostgreSQL connection failed, falling back to SQLite:', err.message);
    isSQLite = true;
    const dbPath = path.join(__dirname, 'db.sqlite3');
    sqliteDb = new sqlite3.Database(dbPath);
    console.log('✅ Using local SQLite database at:', dbPath);
    await createTables(sqliteDb, 'sqlite');
  }
}

async function createTables(db, type) {
  const isPg = type === 'pg';
  const query = isPg ? (text, params) => db.query(text, params) : (text, params) => new Promise((resolve, reject) => {
    db.run(text, params, function(err) {
      if (err) reject(err);
      else resolve(this);
    });
  });

  const schema = [
    `CREATE TABLE IF NOT EXISTS users (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
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
      date_joined ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'},
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'},
      updated_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS service_providers (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER UNIQUE NOT NULL,
      provider_type TEXT DEFAULT 'doctor',
      business_name TEXT NOT NULL,
      license_number TEXT DEFAULT '',
      specialization TEXT DEFAULT '',
      working_hours TEXT DEFAULT '',
      services_offered TEXT DEFAULT '',
      rating REAL DEFAULT 0.0,
      total_reviews INTEGER DEFAULT 0
    )`,
    `CREATE TABLE IF NOT EXISTS otps (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      email TEXT NOT NULL,
      otp_code TEXT NOT NULL,
      otp_type TEXT DEFAULT 'register',
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'},
      is_used INTEGER DEFAULT 0,
      expires_at TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS health_records (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER NOT NULL,
      blood_pressure_systolic INTEGER,
      blood_pressure_diastolic INTEGER,
      blood_sugar REAL,
      weight REAL,
      heart_rate INTEGER,
      temperature REAL,
      oxygen_level INTEGER,
      notes TEXT DEFAULT '',
      recorded_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'},
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS medicines (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      dosage TEXT NOT NULL,
      frequency TEXT DEFAULT 'once',
      start_date TEXT NOT NULL,
      end_date TEXT,
      prescribed_by TEXT DEFAULT '',
      notes TEXT DEFAULT '',
      is_active INTEGER DEFAULT 1,
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS prescriptions (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER NOT NULL,
      doctor_name TEXT NOT NULL,
      hospital_name TEXT DEFAULT '',
      diagnosis TEXT DEFAULT '',
      prescription_date TEXT NOT NULL,
      follow_up_date TEXT,
      document TEXT,
      notes TEXT DEFAULT '',
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS mental_health_logs (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER NOT NULL,
      mood_score INTEGER DEFAULT 3,
      stress_level INTEGER DEFAULT 3,
      sleep_hours REAL,
      sleep_quality INTEGER,
      anxiety_level INTEGER,
      notes TEXT DEFAULT '',
      recorded_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'},
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS insurance_policies (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER NOT NULL,
      policy_type TEXT DEFAULT 'health',
      provider_name TEXT NOT NULL,
      policy_number TEXT NOT NULL,
      coverage_amount REAL NOT NULL,
      premium_amount REAL NOT NULL,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      document TEXT,
      is_active INTEGER DEFAULT 1,
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS lifestyle_logs (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER NOT NULL,
      water_intake INTEGER DEFAULT 0,
      exercise_minutes INTEGER DEFAULT 0,
      steps_count INTEGER DEFAULT 0,
      calories_consumed INTEGER,
      calories_burned INTEGER,
      smoking_count INTEGER DEFAULT 0,
      alcohol_units INTEGER DEFAULT 0,
      notes TEXT DEFAULT '',
      recorded_at ${isPg ? 'DATE DEFAULT CURRENT_DATE' : 'DATE DEFAULT CURRENT_DATE'},
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS activity_logs (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      user_id INTEGER NOT NULL,
      action TEXT DEFAULT 'login',
      details TEXT DEFAULT '',
      ip_address TEXT,
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS system_settings (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      key TEXT UNIQUE NOT NULL,
      value TEXT NOT NULL,
      description TEXT DEFAULT '',
      updated_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS appointments (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      patient_id INTEGER NOT NULL,
      doctor_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      time TEXT NOT NULL,
      reason TEXT NOT NULL,
      status TEXT DEFAULT 'pending',
      type TEXT DEFAULT 'Video Consult',
      meeting_link TEXT,
      notes TEXT DEFAULT '',
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'},
      updated_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`,
    `CREATE TABLE IF NOT EXISTS services (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      provider_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      description TEXT NOT NULL,
      price REAL NOT NULL,
      duration_minutes INTEGER DEFAULT 60,
      is_active INTEGER DEFAULT 1
    )`,
    `CREATE TABLE IF NOT EXISTS service_requests (
      id ${isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'},
      patient_id INTEGER NOT NULL,
      provider_id INTEGER NOT NULL,
      service_name TEXT NOT NULL,
      service_price REAL NOT NULL,
      address TEXT NOT NULL,
      scheduled_date TEXT,
      items TEXT DEFAULT '',
      status TEXT DEFAULT 'pending',
      notes TEXT DEFAULT '',
      created_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'},
      updated_at ${isPg ? 'TIMESTAMPTZ DEFAULT NOW()' : 'DATETIME DEFAULT CURRENT_TIMESTAMP'}
    )`
  ];

  for (const sql of schema) {
    await query(sql);
  }
  console.log('Database tables initialized.');
}

// Wrapper functions
function convertPlaceholders(sql) {
  let i = 0;
  return sql.replace(/\?/g, () => `$${++i}`);
}

async function promisifyDbRun(sql, params = []) {
  if (isSQLite) {
    return new Promise((resolve, reject) => {
      sqliteDb.run(sql, params, function(err) {
        if (err) reject(err);
        else resolve({ id: this.lastID, changes: this.changes });
      });
    });
  } else {
    const pgSql = convertPlaceholders(sql);
    const isInsert = sql.trim().toUpperCase().startsWith('INSERT');
    const finalSql = isInsert && !pgSql.toUpperCase().includes('RETURNING') ? pgSql + ' RETURNING *' : pgSql;
    const result = await pool.query(finalSql, params);
    const row = result.rows ? result.rows[0] : null;
    return { id: row ? row.id : null, changes: result.rowCount };
  }
}

async function promisifyDbAll(sql, params = []) {
  if (isSQLite) {
    return new Promise((resolve, reject) => {
      sqliteDb.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
  } else {
    const pgSql = convertPlaceholders(sql);
    const result = await pool.query(pgSql, params);
    return result.rows;
  }
}

async function promisifyDbGet(sql, params = []) {
  if (isSQLite) {
    return new Promise((resolve, reject) => {
      sqliteDb.get(sql, params, (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  } else {
    const pgSql = convertPlaceholders(sql);
    const result = await pool.query(pgSql, params);
    return result.rows[0] || null;
  }
}

initDatabase().catch(err => console.error('DB init error:', err));

module.exports = {
  pool,
  promisifyDbRun,
  promisifyDbAll,
  promisifyDbGet,
  initDatabase
};
