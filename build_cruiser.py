import os

# --- ARQUITETURA DE CLASSE CRUZADOR ---

# Docker Compose: Agora com Traefik (Proxy) e Redis (Cache)
DOCKER_COMPOSE = """version: '3.8'

services:
  # --- 1. O COMANDANTE (Reverse Proxy & Load Balancer) ---
  traefik:
    image: traefik:v2.10
    container_name: nemesis-bridge
    command:
      - "--api.insecure=true" # Habilita Dashboard
      - "--providers.docker=true" # Escuta o Docker
      - "--providers.docker.exposedbydefault=false" # Segurança: só expõe quem pedir
      - "--entrypoints.web.address=:80" # Porta HTTP
    ports:
      - "80:80"     # Tráfego Web
      - "8080:8080" # Dashboard do Traefik
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - cruiser_net

  # --- 2. O REATOR (Cache de Sessão Ultra-Rápido) ---
  redis-core:
    image: redis:alpine
    container_name: nemesis-reactor
    networks:
      - cruiser_net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # --- 3. O ARQUIVO MORTO (Persistência de Dados) ---
  db-archive:
    image: postgres:15-alpine
    container_name: nemesis-db
    environment:
      POSTGRES_USER: admiral
      POSTGRES_PASSWORD: secure_code_alpha
      POSTGRES_DB: nemesis_logs
    volumes:
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - cruiser_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admiral -d nemesis_logs"]
      interval: 5s
      timeout: 5s
      retries: 5

  # --- 4. ESQUADRÃO DE APLICAÇÃO (Escalável) ---
  app-alpha:
    build: ./app
    container_name: app-alpha
    hostname: alpha-deck
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`nemesis.local`)"
      - "traefik.http.services.app.loadbalancer.server.port=3000"
    environment: &app-env
      DB_HOST: nemesis-db
      DB_USER: admiral
      DB_PASSWORD: secure_code_alpha
      REDIS_HOST: nemesis-reactor
      SESSION_SECRET: MilitaryGradeEncryptionKey
    depends_on:
      redis-core:
        condition: service_healthy
      db-archive:
        condition: service_healthy
    networks:
      - cruiser_net

  app-bravo:
    build: ./app
    container_name: app-bravo
    hostname: bravo-deck
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`nemesis.local`)"
      - "traefik.http.services.app.loadbalancer.server.port=3000"
    environment: *app-env
    depends_on:
      redis-core:
        condition: service_healthy
      db-archive:
        condition: service_healthy
    networks:
      - cruiser_net

  app-charlie:
    build: ./app
    container_name: app-charlie
    hostname: charlie-deck
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`nemesis.local`)"
      - "traefik.http.services.app.loadbalancer.server.port=3000"
    environment: *app-env
    depends_on:
      redis-core:
        condition: service_healthy
      db-archive:
        condition: service_healthy
    networks:
      - cruiser_net

networks:
  cruiser_net:
    driver: bridge
"""

# SQL: Simples e direto, pois o Redis cuidará da sessão pesada
DB_INIT_SQL = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    clearance_level INT DEFAULT 1
);

INSERT INTO users (username, password_hash, full_name, clearance_level) VALUES
('admiral_j', '$2b$10$Q7Zt6P2K7o.pYJ4.x5nNlO3n0j2e.5T6J/0iP8cZq.f.8kYjC.5jW', 'Almirante John', 5),
('ops_officer', '$2b$10$zP6W0.V.a5i.oP8q/A.W5uJ3o.m.2K.D7.b6e.w/Y.jG.y/L.1nK.', 'Oficial Tático', 3);
"""

# Package.json: Adicionando Redis
APP_PACKAGE_JSON = """{
  "name": "nemesis-cruiser-core",
  "version": "2.0.0",
  "main": "server.js",
  "dependencies": {
    "bcrypt": "^5.1.1",
    "connect-redis": "^7.1.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "express": "^4.18.2",
    "express-session": "^1.17.3",
    "helmet": "^7.1.0",
    "ioredis": "^5.3.2",
    "pg": "^8.11.3"
  }
}
"""

APP_DOCKERFILE = """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
"""

# Server.js: Otimizado para Redis e High Availability
APP_SERVER_JS = """require('dotenv').config();
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
"""

# UI: Interface Militar "Sci-Fi"
APP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NEMESIS // CRUISER INTERFACE</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        
        :root { --main-color: #00ff41; --alert-color: #ff3333; --bg-color: #0a0a0a; --glass: rgba(0, 255, 65, 0.1); }
        
        body { 
            background-color: var(--bg-color); 
            color: var(--main-color); 
            font-family: 'Share Tech Mono', monospace; 
            margin: 0; 
            overflow: hidden;
            background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
        }

        /* Scanline Effect */
        body::after {
            content: " ";
            display: block;
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            z-index: 2;
            background-size: 100% 2px, 3px 100%;
            pointer-events: none;
        }

        .container {
            display: grid;
            grid-template-columns: 1fr 3fr 1fr;
            height: 100vh;
            padding: 20px;
            gap: 20px;
            box-sizing: border-box;
            z-index: 10;
            position: relative;
        }

        .panel {
            border: 1px solid var(--main-color);
            padding: 15px;
            background: var(--glass);
            box-shadow: 0 0 10px var(--glass);
            position: relative;
        }

        .panel::before {
            content: ''; position: absolute; top: -2px; left: -2px; width: 10px; height: 10px; border-top: 2px solid var(--main-color); border-left: 2px solid var(--main-color);
        }
        .panel::after {
            content: ''; position: absolute; bottom: -2px; right: -2px; width: 10px; height: 10px; border-bottom: 2px solid var(--main-color); border-right: 2px solid var(--main-color);
        }

        h1, h2 { margin: 0 0 10px 0; border-bottom: 1px solid var(--main-color); text-transform: uppercase; }

        input, button {
            width: 100%; background: black; border: 1px solid var(--main-color); color: var(--main-color); padding: 10px; font-family: inherit; margin-bottom: 10px; font-size: 1.1em;
        }
        button:hover { background: var(--main-color); color: black; cursor: pointer; }

        .metric { font-size: 2em; font-weight: bold; }
        .node-id { color: #fff; text-shadow: 0 0 5px white; }
        
        .hidden { display: none; }
        .blink { animation: blink 1s infinite; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

        #radar {
            width: 100%; height: 200px;
            border-radius: 50%;
            border: 1px solid var(--main-color);
            background: radial-gradient(circle, transparent 20%, rgba(0,255,65,0.1) 21%, transparent 22%);
            position: relative;
            overflow: hidden;
        }
        #radar::after {
            content: ''; position: absolute; top: 50%; left: 50%; width: 50%; height: 2px;
            background: var(--main-color);
            transform-origin: 0 0;
            animation: radar-spin 2s infinite linear;
            box-shadow: 0 0 10px var(--main-color);
        }
        @keyframes radar-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

    </style>
</head>
<body>
    <div class="container">
        <div class="panel">
            <h2>System Status</h2>
            <div id="radar"></div>
            <p>NETWORK: <span class="blink">SECURE</span></p>
            <p>PROXY: TRAEFIK V2</p>
            <p>CACHE: REDIS CLUSTER</p>
            <div style="margin-top: 20px; font-size: 0.8em; color: #888;">
                PROJECT NEMESIS<br>MK-II CRUISER CLASS
            </div>
        </div>

        <div class="panel">
            <div id="login-view">
                <h1>Identity Verification</h1>
                <p>Enter clearance credentials.</p>
                <form id="login-form">
                    <input type="text" id="user" placeholder="OFFICER ID" required autocomplete="off">
                    <input type="password" id="pass" placeholder="ACCESS CODE" required>
                    <button type="submit">AUTHENTICATE</button>
                </form>
                <p id="msg" style="color: var(--alert-color)"></p>
            </div>

            <div id="dashboard-view" class="hidden">
                <h1>Bridge Command</h1>
                <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                    <div style="flex: 1; border: 1px solid #333; padding: 10px;">
                        <small>CURRENT OFFICER</small><br>
                        <span id="off-name" class="metric">---</span>
                    </div>
                    <div style="flex: 1; border: 1px solid #333; padding: 10px;">
                        <small>CLEARANCE</small><br>
                        LEVEL <span id="off-level">0</span>
                    </div>
                </div>
                
                <div style="border: 1px dashed var(--main-color); padding: 20px; text-align: center;">
                    <small>PROCESSING NODE (LB TARGET)</small><br>
                    <span id="proc-node" class="metric node-id">LOADING...</span>
                </div>

                <div style="margin-top: 20px;">
                    <p>SESSION HASH: <span id="sess-id" style="font-size: 0.7em;">---</span></p>
                    <p>REACTOR LINK: <span id="reactor-stat">CHECKING...</span></p>
                </div>

                <button onclick="logout()" style="margin-top: 20px; border-color: var(--alert-color); color: var(--alert-color)">DISENGAGE</button>
            </div>
        </div>

        <div class="panel">
            <h2>Telemetry</h2>
            <div id="logs" style="font-size: 0.8em; height: 90%; overflow: hidden;">
                > INIT_SEQUENCE_START<br>
                > LOADING_CORE_MODULES...<br>
                > CONNECTING_TO_TRAEFIK... OK<br>
                > WAITING_FOR_INPUT...
            </div>
        </div>
    </div>

    <script>
        const logBox = document.getElementById('logs');
        function log(msg) {
            logBox.innerHTML += `> ${msg.toUpperCase()}<br>`;
            logBox.scrollTop = logBox.scrollHeight;
        }

        async function fetchDash() {
            try {
                const res = await fetch('/api/dashboard');
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('off-name').innerText = data.officer.name;
                    document.getElementById('off-level').innerText = data.officer.level;
                    document.getElementById('proc-node').innerText = data.processing_node;
                    document.getElementById('sess-id').innerText = data.session_id.substring(0,20) + '...';
                    document.getElementById('reactor-stat').innerText = data.reactor_status;
                    
                    document.getElementById('login-view').classList.add('hidden');
                    document.getElementById('dashboard-view').classList.remove('hidden');
                    log(`Telemetry received from node ${data.processing_node}`);
                } else {
                    throw new Error('Auth failed');
                }
            } catch (e) {
                document.getElementById('login-view').classList.remove('hidden');
                document.getElementById('dashboard-view').classList.add('hidden');
            }
        }

        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            log('Attempting authentication...');
            const u = document.getElementById('user').value;
            const p = document.getElementById('pass').value;
            
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            });

            if(res.ok) {
                log('Authentication success. Access granted.');
                fetchDash();
            } else {
                log('Authentication failed. Security alert.');
                document.getElementById('msg').innerText = "INVALID CREDENTIALS";
            }
        });

        async function logout() {
            await fetch('/api/logout', {method: 'POST'});
            log('Session terminated.');
            location.reload();
        }

        setInterval(() => {
            if(!document.getElementById('dashboard-view').classList.contains('hidden')) {
                fetchDash(); // Atualiza em tempo real para ver a mudança de nó
            }
        }, 2000);

        fetchDash();
    </script>
</body>
</html>
"""

def build_cruiser():
    print("🛠️ INICIANDO CONSTRUÇÃO DO NEMESIS MK-II (CLASSE CRUZADOR)...")
    
    dirs = ["app", "app/public", "db"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    files = {
        "docker-compose.yml": DOCKER_COMPOSE,
        "db/init.sql": DB_INIT_SQL,
        "app/package.json": APP_PACKAGE_JSON,
        "app/Dockerfile": APP_DOCKERFILE,
        "app/server.js": APP_SERVER_JS,
        "app/public/index.html": APP_HTML
    }
    
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            print(f"✅ Módulo instalado: {path}")

    print("\n🚀 CRUZADOR PRONTO PARA LANÇAMENTO.")
    print("-------------------------------------")
    print("1. Certifique-se que o Docker está rodando.")
    print("2. Edite seu arquivo HOSTS (C:\\Windows\\System32\\drivers\\etc\\hosts) e adicione:")
    print("   127.0.0.1 nemesis.local")
    print("3. Execute: docker compose up --build")
    print("4. Acesse: http://nemesis.local")
    print("5. Painel Tático (Traefik): http://localhost:8080")

if __name__ == "__main__":
    build_cruiser()