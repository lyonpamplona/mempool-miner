# Changelog

Este arquivo segue o formato Keep a Changelog. O projeto ainda não definiu uma
política formal de versionamento.

## Não publicado

### Adicionado

- documentação técnica, operacional, de API, auditoria e roadmap;
- páginas HTML de apresentação e referência da API;
- SVGs animados e READMEs por módulo;
- healthcheck da API, testes unitários, CI, CodeQL, Dependabot e GitHub Pages;
- proxy Nginx same-origin, persistência Redis e redes Docker segmentadas.

### Alterado

- validação e atualização atômica do leaderboard;
- cálculo de taxa em sats/vB;
- encerramento de tarefas, logs e tratamento de falhas;
- grade responsiva, seleção retilínea e renderização segura do ranking;
- ingestão configurada com um único worker.

### Segurança

- credenciais retiradas do bitcoin.conf;
- RPC e Redis deixaram de ser publicados no host;
- sink de XSS persistente removido do frontend principal;
- CORS restringido às origens configuradas.
