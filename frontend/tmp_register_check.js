const http = require('http');
const data = JSON.stringify({
  email: 'testuser@example.com',
  password: 'password123',
  full_name: 'Test User',
});

const options = {
  hostname: 'localhost',
  port: 8000,
  path: '/api/v1/auth/register',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(data),
  },
};

const req = http.request(options, (res) => {
  let body = '';
  res.on('data', (chunk) => {
    body += chunk;
  });
  res.on('end', () => {
    console.log('status', res.statusCode);
    console.log(body);
  });
});

req.on('error', (err) => {
  console.error('error', err.message);
});

req.write(data);
req.end();
