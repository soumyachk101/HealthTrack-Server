const admin = require('firebase-admin');

if (!admin.apps.length) {
  const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT_KEY
    ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY)
    : null;

  if (serviceAccount) {
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      storageBucket: 'healthtracker-88cf8.firebasestorage.app'
    });
  } else {
    admin.initializeApp({
      projectId: 'healthtracker-88cf8',
      storageBucket: 'healthtracker-88cf8.firebasestorage.app'
    });
  }
}

const firestore = admin.firestore();
const firebaseAuth = admin.auth();
const bucket = admin.storage().bucket();

module.exports = { admin, firestore, firebaseAuth, bucket };
