import os

# --- CONTEÚDO DOS ARQUIVOS ---

DOCKER_COMPOSE = """version: '3.8'

services:
  # --- 1. O ORÁCULO (DNS) ---
  dns-oracle:
    build: ./dns
    container_name: dns-oracle
    ports:
      - "53:53/udp"
      - "53:53/tcp"
    networks:
      nemesis_net:
        ipv4_address: 172.28.0.10
    cap_add:
      - NET_ADMIN

  # --- 2. O ARQUIVO (Banco de Dados & Sessão) ---
  db-archive:
    image: postgres:15-alpine
    container_name: db-archive
    hostname: db.nemesis.local
    environment:
      POSTGRES_USER: nemesis_admin
      POSTGRES_PASSWORD: nemesis_secure_password
      POSTGRES_DB: nemesis_db
    volumes:
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      nemesis_net:
        ipv4_address: 172.28.0.20
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nemesis_admin -d nemesis_db"]
      interval: 5s
      timeout: 5s
      retries: 10

  # --- 3, 4, 5. A FROTA (App Servers) ---
  app-pod-1:
    build: ./app
    container_name: app-pod-1
    hostname: app-pod-1
    depends_on:
      db-archive:
        condition: service_healthy
    environment: &app-env
      DB_HOST: 172.28.0.20
      DB_USER: nemesis_admin
      DB_PASSWORD: nemesis_secure_password
      DB_NAME: nemesis_db
      SESSION_SECRET: SegredoEspacialDeAltoNivel2024
    networks:
      nemesis_net:
        ipv4_address: 172.28.1.1

  app-pod-2:
    build: ./app
    container_name: app-pod-2
    hostname: app-pod-2
    depends_on:
      db-archive:
        condition: service_healthy
    environment: *app-env
    networks:
      nemesis_net:
        ipv4_address: 172.28.1.2

  app-pod-3:
    build: ./app
    container_name: app-pod-3
    hostname: app-pod-3
    depends_on:
      db-archive:
        condition: service_healthy
    environment: *app-env
    networks:
      nemesis_net:
        ipv4_address: 172.28.1.3

networks:
  nemesis_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
"""

DNS_DOCKERFILE = """FROM alpine:latest
RUN apk add --no-cache dnsmasq
COPY dnsmasq.conf /etc/dnsmasq.conf
EXPOSE 53/udp 53/tcp
CMD ["dnsmasq", "-k", "--log-queries"]
"""

DNS_CONF = """no-resolv
no-hosts
server=8.8.8.8

# Balanceamento Round Robin: 1 Domínio = 3 IPs
address=/www.meutrabalho.com.br/172.28.1.1
address=/www.meutrabalho.com.br/172.28.1.2
address=/www.meutrabalho.com.br/172.28.1.3

# Rede Interna
address=/db.nemesis.local/172.28.0.20
"""

DB_INIT_SQL = """-- Tabela de Sessão Centralizada (connect-pg-simple)
CREATE TABLE "session" (
  "sid" varchar NOT NULL COLLATE "default",
  "sess" json NOT NULL,
  "expire" timestamp(6) NOT NULL
)
WITH (OIDS=FALSE);
ALTER TABLE "session" ADD CONSTRAINT "session_pkey" PRIMARY KEY ("sid") NOT DEFERRABLE INITIALLY IMMEDIATE;
CREATE INDEX "IDX_session_expire" ON "session" ("expire");

-- Tabela de Usuários
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    rank VARCHAR(50)
);

-- Inserindo Tripulação (Senha: 'password123')
INSERT INTO users (username, password_hash, full_name, rank) VALUES
('cmdr_eva', '$2b$10$Q7Zt6P2K7o.pYJ4.x5nNlO3n0j2e.5T6J/0iP8cZq.f.8kYjC.5jW', 'Eva Rostova', 'Comandante'),
('ops_davis', '$2b$10$zP6W0.V.a5i.oP8q/A.W5uJ3o.m.2K.D7.b6e.w/Y.jG.y/L.1nK.', 'Miles Davis', 'Especialista de Ops');
"""

APP_PACKAGE_JSON = """{
  "name": "nemesis-app",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "jest"
  },
  "dependencies": {
    "bcrypt": "^5.1.1",
    "connect-pg-simple": "^9.0.1",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "express": "^4.18.2",
    "express-session": "^1.17.3",
    "helmet": "^7.1.0",
    "pg": "^8.11.3"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "supertest": "^6.3.3"
  }
}
"""

APP_DOCKERFILE = """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"""

APP_SERVER_JS = """require('dotenv').config();
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
"""

APP_INDEX_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Nemesis Uplink</title>
    <style>
        body { background: #050a14; color: #00f3ff; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .hud { border: 2px solid #00f3ff; padding: 20px; width: 400px; background: rgba(0,0,0,0.9); box-shadow: 0 0 20px rgba(0,243,255,0.2); }
        h2 { text-align: center; border-bottom: 1px solid #00f3ff; padding-bottom: 10px; }
        input, button { width: 100%; padding: 10px; margin: 5px 0; background: transparent; border: 1px solid #00f3ff; color: #00f3ff; box-sizing: border-box; }
        button { background: #00f3ff; color: #000; cursor: pointer; font-weight: bold; }
        button:hover { background: white; }
        .hidden { display: none; }
        #error-log { color: #ff2a2a; text-align: center; margin-top: 10px; min-height: 20px;}
        .status { border-bottom: 1px dashed #00f3ff; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; font-size: 0.8em; }
        .blink { animation: blinker 1s linear infinite; color: red; }
        @keyframes blinker { 50% { opacity: 0; } }
    </style>
</head>
<body>
    <div class="hud">
        <div class="status">
            <span>UPLINK: <span id="conn-status">INICIANDO...</span></span>
            <span>NÓ ATIVO: <span id="active-node">---</span></span>
        </div>

        <div id="login-panel">
            <h2>IDENTIFICAÇÃO DA FROTA</h2>
            <form id="login-form">
                <input type="text" id="username" placeholder="IDENTIFICADOR (ex: cmdr_eva)" required>
                <input type="password" id="password" placeholder="CÓDIGO DE ACESSO" required>
                <button type="submit">INICIAR SESSÃO</button>
            </form>
        </div>

        <div id="profile-panel" class="hidden">
            <h2>DADOS DO TRIPULANTE</h2>
            <p>NOME: <strong id="p-name"></strong></p>
            <p>PATENTE: <span id="p-rank"></span></p>
            <p>ID SESSÃO: <span id="p-sess" style="font-size: 0.8em"></span></p>
            <p style="color: #ffff00; border: 1px solid #ffff00; padding: 5px; text-align: center;">
                PROCESSADO POR:<br><strong id="p-node" style="font-size: 1.2em">---</strong>
            </p>
            <button id="logout-btn" style="background: #ff2a2a; color: white; border-color: #ff2a2a;">ENCERRAR CONEXÃO</button>
        </div>
        <div id="error-log"></div>
    </div>
    <script src="script.js"></script>
</body>
</html>
"""

APP_SCRIPT_JS = """const API = '/api';
const activeNode = document.getElementById('active-node');
const connStatus = document.getElementById('conn-status');

// Heartbeat (Verifica se o servidor está vivo - Ponto Extra)
async function updateTelemetry() {
    try {
        const res = await fetch(`${API}/telemetry`);
        if(res.ok) {
            const data = await res.json();
            activeNode.innerText = data.node;
            connStatus.innerText = "ESTÁVEL";
            connStatus.classList.remove('blink');
            connStatus.style.color = "#00f3ff";
            return true;
        }
    } catch (e) {
        connStatus.innerText = "SINAL PERDIDO (BUSCANDO ROTAS...)";
        connStatus.classList.add('blink');
        activeNode.innerText = "---";
        return false;
    }
}

async function checkSession() {
    const online = await updateTelemetry();
    if(!online) return;

    try {
        const res = await fetch(`${API}/user/profile`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById('p-name').innerText = data.user.name;
            document.getElementById('p-rank').innerText = data.user.rank;
            document.getElementById('p-sess').innerText = data.sessionID.substring(0, 15) + '...';
            document.getElementById('p-node').innerText = data.serverNode;
            
            document.getElementById('login-panel').classList.add('hidden');
            document.getElementById('profile-panel').classList.remove('hidden');
        } else {
            document.getElementById('login-panel').classList.remove('hidden');
            document.getElementById('profile-panel').classList.add('hidden');
        }
    } catch (e) { console.log('Erro de sessão'); }
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    
    try {
        const res = await fetch(`${API}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: u, password: p})
        });
        
        if(res.ok) {
            document.getElementById('error-log').innerText = "";
            checkSession();
        } else {
            document.getElementById('error-log').innerText = ">> ACESSO NEGADO: Credenciais Inválidas";
        }
    } catch(e) {
        document.getElementById('error-log').innerText = ">> ERRO DE COMUNICAÇÃO";
    }
});

document.getElementById('logout-btn').addEventListener('click', async () => {
    await fetch(`${API}/auth/logout`, {method: 'POST'});
    location.reload();
});

// Verifica pulso a cada 2s
setInterval(updateTelemetry, 2000);
checkSession();
"""

APP_TEST_JS = """const request = require('supertest');
const app = require('../server');

// Mock do PG
jest.mock('pg', () => {
  return { Pool: jest.fn(() => ({ query: jest.fn(), on: jest.fn(), connect: jest.fn() })) };
});

describe('Nemesis System Tests', () => {
    test('Telemetria deve estar operacional', async () => {
        const res = await request(app).get('/api/telemetry');
        expect(res.statusCode).toBe(200);
        expect(res.body.status).toBe('OPERATIONAL');
    });

    test('Rota de perfil bloqueada sem login', async () => {
        const res = await request(app).get('/api/user/profile');
        expect(res.statusCode).toBe(401);
    });
});
"""

GITIGNORE = """node_modules
.env
.DS_Store
"""

# --- LÓGICA DE CRIAÇÃO ---

def create_project():
    # Estrutura de pastas
    dirs = [
        "dns",
        "db",
        "app",
        "app/public",
        "app/tests"
    ]
    
    print("🚀 Iniciando construção do Projeto Nemesis...")
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✅ Pasta criada: {d}/")

    # Mapa de arquivos e conteúdos
    files = {
        "docker-compose.yml": DOCKER_COMPOSE,
        ".gitignore": GITIGNORE,
        "dns/Dockerfile": DNS_DOCKERFILE,
        "dns/dnsmasq.conf": DNS_CONF,
        "db/init.sql": DB_INIT_SQL,
        "app/package.json": APP_PACKAGE_JSON,
        "app/Dockerfile": APP_DOCKERFILE,
        "app/server.js": APP_SERVER_JS,
        "app/public/index.html": APP_INDEX_HTML,
        "app/public/script.js": APP_SCRIPT_JS,
        "app/tests/basic.test.js": APP_TEST_JS
    }

    for filepath, content in files.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 Arquivo gerado: {filepath}")

    print("\n🎉 MISSÃO CUMPRIDA! Estrutura criada com sucesso.")
    print("---------------------------------------------------")
    print("👉 PRÓXIMO PASSO: Execute 'docker-compose up --build'")

if __name__ == "__main__":
    create_project()