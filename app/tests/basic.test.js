const request = require('supertest');
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
