# Política de Badges do README

Esta política aplica-se sempre que um agente criar, alterar ou rever `README.md` ou `README.template.md`.

## Regra principal

Todo README técnico deve ter badges no topo que representem o estado do projeto e as tecnologias realmente usadas.

Os badges não são decoração. Servem para comunicar rapidamente stack, maturidade, licença, build/testes e modo de execução.

## Fonte da Verdade

Antes de adicionar badges de tecnologias, o agente deve inferir a stack a partir de fontes reais do repositório:

- `package.json`, `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`;
- `composer.json`, `composer.lock`;
- `pyproject.toml`, `requirements.txt`, `poetry.lock`, `uv.lock`;
- `Dockerfile`, `compose.yml`, `docker-compose.yml`;
- `VERSION`;
- `LICENSE`;
- `.csproj`, `.sln`, `global.json`;
- `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`;
- ficheiros de configuração de frameworks;
- estrutura real do código.

Não adicionar badge de uma tecnologia apenas porque é comum, desejável ou mencionada em texto antigo.

## Badges Obrigatórios

Quando aplicável, o README deve conter:

1. **Estado** — `active`, `stable`, `experimental`, `maintenance` ou `archived`.
2. **Licença** — licença real, declaração proprietária ou `A confirmar` apenas quando ainda não existir decisão.
3. **Stack principal** — frontend, backend, linguagem principal, DB e infra, conforme existam.
4. **Build/Testes** — badge real de CI se existir; badge estático apenas se não houver pipeline.
5. **Versão** — obrigatório em modelos/packs versionados; opcional em apps sem versão SemVer formal.

## Regras de Honestidade

- Remover badges de tecnologias não usadas.
- Usar `A confirmar` apenas em modelos ou quando o utilizador ainda não definiu a informação.
- Não usar badges de CI/CD se não existir pipeline real.
- Não usar badge `passing` se os testes não foram executados ou não há pipeline.
- Não usar licença específica se o repositório não tiver licença confirmada em `LICENSE` ou instrução explícita do titular.
- Não duplicar badges equivalentes.

## Ordem recomendada

```md
# <NOME_DO_PROJETO>

![Estado](...)
![Versão](...)
![Licença](...)
![Frontend](...)
![Backend](...)
![Database](...)
![Docker](...)
![Tests](...)
```

Manter apenas os badges relevantes.

## Exemplos de Badges Estáticos

### Estado / Projeto

```md
![Estado](https://img.shields.io/badge/estado-active-2ecc71)
![Versão](https://img.shields.io/badge/vers%C3%A3o-0.1.0-3498db)
![Licença](https://img.shields.io/badge/licen%C3%A7a-propriet%C3%A1ria-lightgrey)
```

### Frontend

```md
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Material UI](https://img.shields.io/badge/MUI-007FFF?logo=mui&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
```

### Backend

```md
![Node.js](https://img.shields.io/badge/Node.js-339933?logo=nodedotjs&logoColor=white)
![Express](https://img.shields.io/badge/Express-000000?logo=express&logoColor=white)
![LoopBack](https://img.shields.io/badge/LoopBack-3F5DFF?logo=loopback&logoColor=white)
![PHP](https://img.shields.io/badge/PHP-777BB4?logo=php&logoColor=white)
![Laravel](https://img.shields.io/badge/Laravel-FF2D20?logo=laravel&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![.NET](https://img.shields.io/badge/.NET-512BD4?logo=dotnet&logoColor=white)
```

### Base de Dados / Infraestrutura

```md
![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-003545?logo=mariadb&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL_Server-CC2927?logo=microsoftsqlserver&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)
```

### Qualidade

```md
![Tests](https://img.shields.io/badge/tests-A%20confirmar-lightgrey)
![Build](https://img.shields.io/badge/build-A%20confirmar-lightgrey)
```

## Modelo Mínimo

```md
# <NOME_DO_PROJETO>

![Estado](https://img.shields.io/badge/estado-A%20confirmar-lightgrey)
![Versão](https://img.shields.io/badge/vers%C3%A3o-0.1.0-3498db)
![Licença](https://img.shields.io/badge/licen%C3%A7a-propriet%C3%A1ria-lightgrey)
![Stack](https://img.shields.io/badge/stack-A%20confirmar-lightgrey)
```

Substituir `Stack` por badges reais assim que a tecnologia for conhecida.


## Integração com VERSION e LICENSE

Quando existirem `VERSION` e `LICENSE` na raiz:

- o badge de versão deve refletir `VERSION`;
- o badge de licença deve refletir `LICENSE`;
- se `LICENSE` for proprietária, usar badge `licença-proprietária`;
- se a licença for open-source, usar o identificador conhecido, por exemplo `MIT`, `Apache--2.0` ou `GPL--3.0`;
- não deixar badge `A confirmar` quando `LICENSE` já contém uma decisão explícita.
