const http = require('http');

const data = JSON.stringify({
  username: "soumya933",
  password: "password123" // Just guessing, or I can create a new user!
});

const req = http.request({
  hostname: 'localhost',
  port: 8000,
  path: '/accounts/api/login/',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
}, res => {
  let body = '';
  res.on('data', d => body += d);
  res.on('end', () => console.log(body));
});
req.write(data);
req.end();
