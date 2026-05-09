require('dotenv').config();
const nodemailer = require('nodemailer');

const emailUser = process.env.EMAIL_HOST_USER;
const emailPass = process.env.EMAIL_HOST_PASSWORD;

console.log("User:", emailUser);
console.log("Pass:", emailPass ? "***" : "missing");

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: emailUser,
    pass: emailPass
  }
});

transporter.sendMail({
  from: `"HealthTrack+ (No-Reply)" <${emailUser}>`,
  to: "soumya.chk101@gmail.com",
  subject: "Test Email",
  text: "This is a test email"
}).then(info => {
  console.log("Success!", info.messageId);
}).catch(err => {
  console.error("Error sending:", err);
});
