# Política de segurança

## Versões suportadas

Enquanto o projeto não possui releases estáveis, somente a branch main recebe
correções de segurança.

## Como reportar

Não abra uma issue pública com credenciais, provas de conceito exploráveis ou
dados do nó. Em um repositório GitHub, use **Security → Report a
vulnerability** para criar um advisory privado. Inclua:

- versão/commit afetado;
- pré-condições e impacto;
- passos mínimos de reprodução;
- correção sugerida, se houver;
- logs já sanitizados.

## Segredos

O arquivo .env é local e ignorado pelo Git. Se uma credencial RPC já tiver sido
publicada, removê-la do arquivo não é suficiente: rotacione-a e avalie o
histórico do repositório.

## Escopo conhecido

O leaderboard ainda confia na pontuação enviada pelo navegador. Isso é um risco
de integridade conhecido e está documentado no roadmap; não trate o ranking
atual como prova de saldo, mineração ou propriedade de Bitcoin.
