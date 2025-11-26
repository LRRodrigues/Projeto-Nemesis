
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
