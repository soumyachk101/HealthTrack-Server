require('dotenv').config();
const { pool } = require('./db');

async function checkUsers() {
    const client = await pool.connect();
    try {
        const res = await client.query('SELECT id, username, email, user_type, is_superuser FROM users');
        console.log('Users in database:');
        console.table(res.rows);
    } catch (err) {
        console.error('Error querying database:', err);
    } finally {
        client.release();
        process.exit();
    }
}

checkUsers();
