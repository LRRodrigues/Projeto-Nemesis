# PROJECT NEMESIS 🛰️
### MK-II CRUISER CLASS ARCHITECTURE

```text
 _   _  _____  __  __  _____  _____  ___  _____ 
| \ | || ____||  \/  || ____|/ ____||_ _|| ____|
|  \| ||  _|  | |\/| ||  _| | (___   | | |  _|  
| |\  || |___ | |  | || |___ \___ \  | | | |___ 
|_| \_||_____||_|  |_||_____||_____/ |___||_____|
          :: SYSTEM OPERATIONAL ::
📋 Mission Briefing (Resumo)
O Projeto Nemesis MK-II representa um salto evolutivo em arquitetura de aplicações distribuídas. Diferente de sua versão anterior (MK-I), que dependia de balanceamento DNS simples, esta nova classe implementa uma Arquitetura de Microsserviços Cloud-Native.

O objetivo é demonstrar alta disponibilidade, persistência de sessão distribuída (Distributed Caching) e observabilidade em tempo real, utilizando um Proxy Reverso Inteligente para orquestrar o tráfego entre múltiplos nós de processamento.

🏗️ Arquitetura do Sistema
O sistema opera sob uma topologia de cluster containerizado, onde o tráfego é interceptado e roteado dinamicamente.

graph TD
    user((Tripulante / Cliente))
    
    subgraph "NEMESIS CRUISER CLUSTER"
        style proxy fill:#f96,stroke:#333,stroke-width:2px
        style redis fill:#d64,stroke:#333,stroke-width:2px
        style db fill:#69b,stroke:#333,stroke-width:2px
        
        proxy[TRAEFIK EDGE ROUTER<br/>Load Balancer & Dashboard]
        
        subgraph "Application Deck (Escalável)"
            node1[Node Alpha]
            node2[Node Bravo]
            node3[Node Charlie]
        end
        
        redis[(REDIS REACTOR<br/>Session Cache)]
        db[(POSTGRES ARCHIVE<br/>User Data)]
    end

    user -->|HTTP Request| proxy
    proxy -->|Round Robin| node1
    proxy -->|Round Robin| node2
    proxy -->|Round Robin| node3
    
    node1 <-->|Leitura/Escrita Sessão <1ms| redis
    node2 <-->|Leitura/Escrita Sessão <1ms| redis
    node3 <-->|Leitura/Escrita Sessão <1ms| redis
    
    node1 -->|Persistência Dados| db
    node2 -->|Persistência Dados| db
    node3 -->|Persistência Dados| db
🔧 Componentes Táticos
Traefik (The Bridge): Atua como Proxy Reverso e Load Balancer. Substitui o DNS Round Robin antigo por um roteamento inteligente L7 (Camada de Aplicação), permitindo health checks ativos e remoção automática de contêineres falhos.

Redis (The Reactor): Armazena o estado das sessões dos usuários em memória (RAM). Isso permite que um usuário "pule" entre servidores (nós) sem nunca ser deslogado, com latência sub-milissegundo.

Node.js Cluster (The Fleet): 3 instâncias da aplicação (alpha, bravo, charlie) rodando simultaneamente, servindo a interface tática.

PostgreSQL (The Archive): Armazenamento persistente e seguro das credenciais e logs históricos.

🚀 Protocolo de Lançamento (Instalação)
Pré-requisitos
Docker Desktop (com WSL 2 no Windows).

Portas 80 e 8080 livres.

1. Configuração de DNS Local
Para simular um ambiente de produção real, mapeamos o domínio da nave para o localhost.

Windows: Abra o Bloco de Notas como Administrador e edite C:\Windows\System32\drivers\etc\hosts.

Linux/Mac: Edite /etc/hosts.

Adicione a seguinte linha:

127.0.0.1 nemesis.local
2. Inicialização dos Reatores
No terminal, dentro da pasta do projeto:

docker compose up --build
Aguarde a estabilização dos logs.

🎮 Manual de Operações
Acesso à Interface Tática (Aplicação)
O sistema estará disponível no domínio configurado.

URL: http://nemesis.local

Credenciais de Acesso (Nível Almirante):

User: admiral_j

Pass: password123

Telemetria e Engenharia (Dashboard)
Para visualizar o balanceamento de carga acontecendo em tempo real (visão do Engenheiro).

URL: http://localhost:8080

Explore as abas HTTP Services para ver os nós alpha, bravo e charlie em operação.

🧪 Testes de Resiliência (Failover)
Para provar a robustez do sistema MK-II:

Logue no sistema em http://nemesis.local.

Observe o campo PROCESSING NODE (ex: alpha-deck).

"Derrube" esse servidor propositalmente:

docker stop app-alpha
Atualize a página (F5).

Resultado: O Traefik redirecionará instantaneamente para bravo ou charlie. O Redis manterá sua sessão ativa. O usuário não percebe a falha.

🛠️ Tech Stack
Backend: Node.js (Express)

Frontend: HTML5/CSS3 (Retro-Futuristic Design)

Database: PostgreSQL 15

Cache: Redis 7 (Alpine)

Proxy: Traefik v2.10

Containerization: Docker & Docker Compose

"Ad Astra Per Aspera" - Projeto Nemesis