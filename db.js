const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = process.env.DATABASE_URL || path.join(__dirname, 'db.sqlite3');

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
  } else {
    console.log('Connected to SQLite database.');
    initDatabase();
  }
});

function initDatabase() {
  db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      first_name TEXT DEFAULT '',
      last_name TEXT DEFAULT '',
      user_type TEXT DEFAULT 'patient' CHECK(user_type IN ('patient','provider','admin')),
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
      date_joined TEXT DEFAULT CURRENT_TIMESTAMP,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS service_providers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER UNIQUE NOT NULL,
      provider_type TEXT DEFAULT 'doctor' CHECK(provider_type IN ('hospital','clinic','pharmacy','lab','doctor')),
      business_name TEXT NOT NULL,
      license_number TEXT DEFAULT '',
      specialization TEXT DEFAULT '',
      working_hours TEXT DEFAULT '',
      services_offered TEXT DEFAULT '',
      rating REAL DEFAULT 0.0,
      total_reviews INTEGER DEFAULT 0,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS otps (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT NOT NULL,
      otp_code TEXT NOT NULL,
      otp_type TEXT DEFAULT 'register' CHECK(otp_type IN ('register','login','password_reset')),
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      is_used INTEGER DEFAULT 0,
      expires_at TEXT NOT NULL
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS health_records (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      blood_pressure_systolic INTEGER,
      blood_pressure_diastolic INTEGER,
      blood_sugar REAL,
      weight REAL,
      heart_rate INTEGER,
      temperature REAL,
      oxygen_level INTEGER,
      notes TEXT DEFAULT '',
      recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS medicines (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      dosage TEXT NOT NULL,
      frequency TEXT DEFAULT 'once' CHECK(frequency IN ('once','twice','thrice','asneeded')),
      start_date TEXT NOT NULL,
      end_date TEXT,
      prescribed_by TEXT DEFAULT '',
      notes TEXT DEFAULT '',
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS prescriptions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      doctor_name TEXT NOT NULL,
      hospital_name TEXT DEFAULT '',
      diagnosis TEXT DEFAULT '',
      prescription_date TEXT NOT NULL,
      follow_up_date TEXT,
      document TEXT,
      notes TEXT DEFAULT '',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS mental_health_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      mood_score INTEGER DEFAULT 3 CHECK(mood_score IN (1,2,3,4,5)),
      stress_level INTEGER DEFAULT 3 CHECK(stress_level IN (1,2,3,4,5)),
      sleep_hours REAL,
      sleep_quality INTEGER CHECK(sleep_quality IN (1,2,3,4,5)),
      anxiety_level INTEGER CHECK(anxiety_level IN (1,2,3,4,5)),
      notes TEXT DEFAULT '',
      recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS insurance_policies (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      policy_type TEXT DEFAULT 'health' CHECK(policy_type IN ('health','life','term')),
      provider_name TEXT NOT NULL,
      policy_number TEXT NOT NULL,
      coverage_amount REAL NOT NULL,
      premium_amount REAL NOT NULL,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      document TEXT,
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS lifestyle_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      water_intake INTEGER DEFAULT 0,
      exercise_minutes INTEGER DEFAULT 0,
      steps_count INTEGER DEFAULT 0,
      calories_consumed INTEGER,
      calories_burned INTEGER,
      smoking_count INTEGER DEFAULT 0,
      alcohol_units INTEGER DEFAULT 0,
      notes TEXT DEFAULT '',
      recorded_at TEXT DEFAULT CURRENT_DATE,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      UNIQUE(user_id, recorded_at)
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS activity_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      action TEXT DEFAULT 'login' CHECK(action IN ('login','logout','record_added','medicine_added','prescription_added','profile_updated','registration','appointment_booked','service_requested','admin_action')),
      details TEXT DEFAULT '',
      ip_address TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS system_settings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT UNIQUE NOT NULL,
      value TEXT NOT NULL,
      description TEXT DEFAULT '',
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS appointments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id INTEGER NOT NULL,
      doctor_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      time TEXT NOT NULL,
      reason TEXT NOT NULL,
      status TEXT DEFAULT 'pending' CHECK(status IN ('pending','confirmed','completed','cancelled')),
      type TEXT DEFAULT 'Video Consult',
      meeting_link TEXT,
      notes TEXT DEFAULT '',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS services (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      provider_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      description TEXT NOT NULL,
      price REAL NOT NULL,
      duration_minutes INTEGER DEFAULT 60,
      is_active INTEGER DEFAULT 1,
      FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS service_requests (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patient_id INTEGER NOT NULL,
      provider_id INTEGER NOT NULL,
      service_name TEXT NOT NULL,
      service_price REAL NOT NULL,
      address TEXT NOT NULL,
      scheduled_date TEXT,
      items TEXT DEFAULT '',
      status TEXT DEFAULT 'pending' CHECK(status IN ('pending','accepted','completed','declined','cancelled')),
      notes TEXT DEFAULT '',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE
    )`);

    db.run(`CREATE INDEX IF NOT EXISTS idx_health_records_user ON health_records(user_id)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_medicines_user ON medicines(user_id)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_prescriptions_user ON prescriptions(user_id)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_otps_email ON otps(email)`);
  });
}

function promisifyDb(method) {
  return function(sql, params = []) {
    return new Promise((resolve, reject) => {
      db[method](sql, params, function(err, result) {
        if (err) reject(err);
        else resolve(result);
      });
    });
  };
}

function promisifyDbRun(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function(err) {
      if (err) reject(err);
      else resolve({ id: this.lastID, changes: this.changes });
    });
  });
}

function promisifyDbAll(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

function promisifyDbGet(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

module.exports = {
  db,
  promisifyDbRun,
  promisifyDbAll,
  promisifyDbGet,
  initDatabase
};
