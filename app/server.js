require('dotenv').config();
const express = require('express');
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const Redis = require('ioredis');
const { Pool } = require('pg');
const helmet = require('helmet');
const cors = require('cors');
const bcrypt = require('bcrypt');
const os = require('os');

const app = express();

// --- CONEXÃO COM O REATOR (REDIS) ---
const redisClient = new Redis({
  host: process.env.REDIS_HOST,
  port: 6379
});

// --- CONEXÃO COM O ARQUIVO (POSTGRES) ---
const pgPool = new Pool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: 'nemesis_logs'
});

app.use(helmet({ contentSecurityPolicy: false })); // Ajuste para UI militar
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// --- SESSÃO DISTRIBUÍDA DE ALTA PERFORMANCE ---
app.use(session({
  store: new RedisStore({ client: redisClient, prefix: 'nemesis:' }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 1000 * 60 * 60 * 24, httpOnly: true, secure: false }
}));

// --- SISTEMAS DE BORDO ---
app.get('/api/status', (req, res) => {
  res.json({
    system: 'NOMINAL',
    node: os.hostname(),
    memory: process.memoryUsage().rss,
    uptime: process.uptime()
  });
});

app.post('/api/login', async (req, res) => {
  const { username, password } = req.body;
  try {
    const { rows } = await pgPool.query('SELECT * FROM users WHERE username = $1', [username]);
    if (rows.length > 0) {
      const match = await bcrypt.compare(password, rows[0].password_hash);
      if (match) {
        req.session.user = { 
            id: rows[0].id, 
            name: rows[0].full_name, 
            level: rows[0].clearance_level 
        };
        return res.json({ status: 'ACCESS_GRANTED', clearance: rows[0].clearance_level });
      }
    }
    res.status(401).json({ status: 'ACCESS_DENIED' });
  } catch (err) { res.status(500).json({ status: 'SYSTEM_FAILURE' }); }
});

app.post('/api/logout', (req, res) => {
  req.session.destroy();
  res.json({ status: 'SESSION_TERMINATED' });
});

app.get('/api/dashboard', (req, res) => {
  if (!req.session.user) return res.status(403).json({ status: 'UNAUTHORIZED' });
  res.json({
    officer: req.session.user,
    processing_node: os.hostname(),
    session_id: req.sessionID,
    reactor_status: redisClient.status
  });
});

app.listen(3000, () => console.log(`[${os.hostname()}] Nemesis Node Online`));
