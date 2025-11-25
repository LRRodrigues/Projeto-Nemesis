require('dotenv').config();
const express = require('express');
const session = require('express-session');
const PgSession = require('connect-pg-simple')(session);
const { Pool } = require('pg');
const helmet = require('helmet');
const cors = require('cors');
const bcrypt = require('bcrypt');
const os = require('os');

const app = express();
const PORT = 3000;

const pool = new Pool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: 5432
});

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// SESSÃO CENTRALIZADA (Persistência no DB)
app.use(session({
  store: new PgSession({ pool: pool, tableName: 'session' }),
  secret: process.env.SESSION_SECRET || 'segredo',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 3600000, httpOnly: true, secure: false }
}));

// Rota de Pulso (Telemetria)
app.get('/api/telemetry', (req, res) => {
  res.json({ node: os.hostname(), status: 'OPERATIONAL' });
});

// Login
app.post('/api/auth/login', async (req, res) => {
  const { username, password } = req.body;
  try {
    const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
    if (result.rows.length > 0) {
      const user = result.rows[0];
      if (await bcrypt.compare(password, user.password_hash)) {
        req.session.userId = user.id;
        req.session.user = { name: user.full_name, rank: user.rank };
        return res.json({ message: 'OK' });
      }
    }
    res.status(401).json({ error: 'Falha na autenticação' });
  } catch (err) { res.status(500).json({ error: 'Erro interno' }); }
});

// Logout
app.post('/api/auth/logout', (req, res) => {
  req.session.destroy();
  res.clearCookie('connect.sid');
  res.json({ message: 'Logout OK' });
});

// Perfil Protegido
app.get('/api/user/profile', (req, res) => {
  if (!req.session.userId) return res.status(401).json({ error: 'Não autorizado' });
  res.json({
    user: req.session.user,
    sessionID: req.sessionID,
    serverNode: os.hostname()
  });
});

app.listen(PORT, '0.0.0.0', () => console.log(`🚀 Nó ${os.hostname()} online.`));
module.exports = app;
