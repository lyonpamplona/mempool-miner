# Implantação

## Perfil atual

O Compose entregue é um ambiente local endurecido, não uma topologia pronta
para dinheiro real. Somente Nginx publica porta e o bind é localhost.

## Checklist antes de expor

- [ ] TLS e HSTS em proxy de borda;
- [ ] identidade do jogador e score calculado no servidor;
- [ ] rate limiting REST/WebSocket;
- [ ] validação de Origin no WebSocket;
- [ ] rpcauth/secret manager e rotação;
- [ ] subnet RPC exata;
- [ ] lock com hashes, SBOM e imagens por digest;
- [ ] Nginx não-root, capabilities mínimas e filesystem somente leitura;
- [ ] rotação de logs e limites de recursos verificados no runtime;
- [ ] backup/restauração testados;
- [ ] observabilidade e alertas;
- [ ] ingestão separada da API;
- [ ] política de privacidade e licença definidas.

## Escala

Não aumente workers do backend atual. Cada worker assinaria ZMQ e duplicaria
eventos. Primeiro extraia um serviço ingestor singleton e publique eventos em
um stream durável; depois escale apenas gateways REST/WebSocket.

## TLS

O frontend já usa URLs same-origin e escolhe ws/wss conforme o protocolo.
Termine TLS antes do Nginx interno ou substitua-o pelo proxy corporativo,
preservando /api, /ws, Upgrade e timeouts.

## Mainnet

Mainnet aumenta tráfego, disco, tempo de sincronização e consequências
operacionais. O nó está em modo pruned e txindex desabilitado. Antes de trocar:

1. use volume novo;
2. altere BITCOIN_NETWORK=main e RPC_PORT=8332;
3. revise prune/disk/memória;
4. teste a taxa da fila;
5. confirme que nenhum RPC está publicado;
6. substitua a imagem de laboratório por cadeia de fornecimento verificada.

## Rollback

Imagens e configuração devem ser versionadas juntas. Preserve o volume, reverta
o commit, restaure a tag anterior e suba. Downgrade de Bitcoin Core pode não
aceitar dados produzidos por versão nova; valide em cópia antes.
