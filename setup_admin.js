require('dotenv').config();
const bcrypt = require('bcryptjs');
const { promisifyDbRun, promisifyDbGet } = require('./db');

async function setupAdmin() {
    const username = 'soumya933';
    const email = 'soumya.chk101@gmail.com';
    const password = 'Soumya@2842y';
    
    console.log(`Setting up admin user: ${username}...`);
    
    try {
        const hashedPassword = await bcrypt.hash(password, 10);
        
        // Check if user exists
        const existingUser = await promisifyDbGet('SELECT id FROM users WHERE username = ? OR email = ?', [username, email]);
        
        if (existingUser) {
            console.log('User already exists, updating to Admin...');
            await promisifyDbRun(
                'UPDATE users SET password = ?, user_type = ?, is_superuser = ?, is_approved = ?, is_email_verified = ? WHERE id = ?',
                [hashedPassword, 'admin', 1, 1, 1, existingUser.id]
            );
            console.log('✅ Admin user updated successfully.');
        } else {
            console.log('Creating new Admin user...');
            await promisifyDbRun(
                'INSERT INTO users (username, email, password, user_type, is_approved, is_superuser, is_email_verified) VALUES (?, ?, ?, ?, ?, ?, ?)',
                [username, email, hashedPassword, 'admin', 1, 1, 1]
            );
            console.log('✅ Admin user created successfully.');
        }
    } catch (err) {
        console.error('❌ Error setting up admin:', err.message);
    } finally {
        process.exit();
    }
}

setupAdmin();
