const API = '/api';
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
