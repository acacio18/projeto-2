# Evidência — E0: acesso ao repositório remoto (25/10/2026)

- **Repositório oficial:** `git@github.com:acacio18/projeto-2.git` (público, branch padrão `main`). Substitui o `acacio18/SUAP-V2`, abandonado por decisão do usuário.
- **Chave:** ed25519 gerada nesta máquina em `C:\Users\Pichau\.ssh\id_ed25519_suapv2` (impressão digital `SHA256:7dsl0jepfPwqua4pUBrXlj0om8p/arIRiKi41as0hRo`), cadastrada pelo usuário como **deploy key com escrita** no `projeto-2`. `~/.ssh/config` aponta essa chave para `github.com`.
- **Chave do host GitHub** registrada em `~/.ssh/known_hosts` após conferir a impressão digital oficial `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU`.
- **Observação técnica:** o OpenSSH do Windows (`C:\Windows\System32\OpenSSH`) não negocia com o GitHub ("unsupported KEX method"). O Git usa o SSH próprio (`C:\Program Files\Git\usr\bin\ssh.exe`, OpenSSH 10.6), que funciona.

| Teste | Comando | Resultado |
|---|---|---|
| Autenticação | `ssh -T git@github.com` | `Hi acacio18/projeto-2! You've successfully authenticated…` |
| Leitura | `git ls-remote git@github.com:acacio18/projeto-2.git` | `main` em `5c44c5d` |
| Escrita | `git push --dry-run origin main` | `Everything up-to-date`, código 0 (nada enviado) |

**Conteúdo encontrado no repositório (3 commits):** `svgs/icon-cog.svg` e `svgs/icon.trophy.svg` (vazios, 0 bytes), `.gitignore` (modelo Laravel/PHP), `README.md` (genérico). Limpeza proposta (remover os SVGs; trocar `.gitignore` e README) **aguardando autorização**.
