-- Tabela de Sessão Centralizada (connect-pg-simple)
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
