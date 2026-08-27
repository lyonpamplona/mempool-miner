<p align="center"><img src="assets/mempool-miner-banner.svg" width="100%" alt="Mempool Miner"></p>

# Portal de documentação

Este diretório contém duas camadas distintas:

- documentação técnica Markdown, versionada para mantenedores do repositório;
- portal público sanitizado, construído por allowlist a partir de `index.html`,
  `api.html`, `site.css` e `assets/`.

O contêiner público não copia Markdown, relatórios internos, configuração,
Swagger nem OpenAPI bruto. Relatórios de trabalho locais devem usar
`internal-docs/`, que é ignorado pelo Git.

## Trilhas de leitura

- Quero executar: [CONFIGURACAO.md](CONFIGURACAO.md) →
  [TUTORIAL.md](TUTORIAL.md) → [COMANDOS.md](COMANDOS.md).
- Quero desenvolver: [ARQUITETURA.md](ARQUITETURA.md) →
  [MULTI_REDE.md](MULTI_REDE.md) → [FLUXOS.md](FLUXOS.md) →
  [MECANICAS.md](MECANICAS.md) → [MODULOS.md](MODULOS.md) → [API.md](API.md).
- Quero corrigir riscos: [SEGURANCA.md](SEGURANCA.md) →
  [AUDITORIA.md](AUDITORIA.md) → [ROADMAP.md](ROADMAP.md).
- Estou com erro: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Portal público

- [Visão geral sanitizada](index.html)
- [Referência visual da API](api.html)

Na stack local, o portal usa um serviço opcional separado do jogo:

```powershell
docker compose --profile docs up -d --build docs
```

- portal: `http://localhost:8010/`;
- API pública: `http://localhost:8010/api/`;
- apresentação: `http://localhost:8010/apresentacao/`.

Os SVGs em [assets](assets/) possuem título, descrição e alternativa sem
movimento para usuários com preferência de animação reduzida.
