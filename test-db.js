const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const dbPath = path.join(__dirname, 'server', 'db.sqlite3');
const db = new sqlite3.Database(dbPath);

db.all('SELECT id, username, user_type FROM users', [], (err, rows) => {
  if (err) console.error(err);
  else console.log("USERS:", rows);
});
db.all('SELECT * FROM service_providers', [], (err, rows) => {
  if (err) console.error(err);
  else console.log("PROVIDERS:", rows);
});
