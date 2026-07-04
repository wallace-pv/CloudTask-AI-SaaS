# Mapa de scripts — por semana

Índice único de **todos os scripts executáveis** do projeto: o que cada um faz,
de **qual semana/aula** é e **como rodar**. Se ficou em dúvida sobre um script,
comece por aqui.

## Convenção de nomes e pastas

Cada script diz a semana **pelo nome ou pela pasta**:

* **Utilitários soltos** ficam em `scripts/semana-NN-tema/` — a **pasta** diz a
  semana (ex.: `scripts/semana-04-ecr/`).
* **Scripts presos a um subsistema** (que precisam rodar de dentro da pasta dele
  por causa de caminhos relativos) ficam na pasta do subsistema com o **prefixo
  `semana-NN-` no nome** (ex.: `infra/cdk/semana-06-cdk-deploy.sh`).
* Todo script tem, no topo, um banner **`Semana N · Aula NN — propósito`**.

## Tabela

| Semana | Aula | Script | O que faz | Como rodar |
| --- | --- | --- | --- | --- |
| — (setup) | — | [`.devcontainer/post-create.sh`](../.devcontainer/post-create.sh) | Instala `eksctl` + AWS CDK e ajusta credenciais ao criar o devcontainer. | Automático (o VS Code roda ao abrir o container). |
| **4** | 7 | [`scripts/semana-04-ecr/build-push-ecr.sh`](semana-04-ecr/build-push-ecr.sh) | Build da imagem `prod` + push para o **Amazon ECR** (cria o repo se faltar). | `./scripts/semana-04-ecr/build-push-ecr.sh` (na raiz do repo) |
| **5** | 9 | [`scripts/semana-05-hpa/teste-carga.py`](semana-05-hpa/teste-carga.py) | Teste de carga (stdlib) para **ver o HPA escalar**. | `python scripts/semana-05-hpa/teste-carga.py --url http://<LB>/tasks` |
| **6** | 11 | [`infra/cdk/semana-06-cdk-deploy.sh`](../infra/cdk/semana-06-cdk-deploy.sh) | Sobe/derruba as **7 stacks CDK** no Academy (sem `cdk bootstrap`). | `cd infra/cdk && ./semana-06-cdk-deploy.sh deploy` \| `destroy` |
| **6** | 12 | [`infra/servers/semana-06-servidores-subir.sh`](../infra/servers/semana-06-servidores-subir.sh) | Cria o SG e sobe os **3 EC2** (API + Frontend + Grafana); imprime os links. | `bash infra/servers/semana-06-servidores-subir.sh` |
| **6** | 12 | [`infra/servers/semana-06-servidores-destruir.sh`](../infra/servers/semana-06-servidores-destruir.sh) | Termina os 3 EC2 (tag `project=cloudtask-demo`) e apaga o SG. | `bash infra/servers/semana-06-servidores-destruir.sh` |

### Arquivos de apoio (não rode direto)

| Arquivo | Papel | Semana |
| --- | --- | --- |
| [`infra/servers/userdata-api.sh`](../infra/servers/userdata-api.sh) | `user-data` do EC2 da API (lido pelo `…-subir.sh` e pela `ComputeStack`). | 6 |
| [`infra/servers/userdata-grafana.sh`](../infra/servers/userdata-grafana.sh) | `user-data` do EC2 do Grafana. | 6 |
| [`infra/servers/grafana-dashboard.json`](../infra/servers/grafana-dashboard.json) | Dashboard provisionado no Grafana. | 6 |
| [`buildspec.yml`](../buildspec.yml) | Receita do AWS CodeBuild (CI da imagem). | 4 |
| `docker-compose*.yml` | Subir API+banco local / rodar testes. | 1–2 |

> ℹ️ Os `userdata-*.sh` e o `grafana-dashboard.json` **mantêm o nome** (sem
> prefixo de semana) porque são lidos **por nome** pelo
> `infra/servers/semana-06-servidores-subir.sh` e pelo
> `infra/cdk/stacks/compute_stack.py`. A pasta `infra/servers/` já indica que
> são da Semana 6.
