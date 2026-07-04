# Relatório Final — CloudTask AI SaaS

> **Trabalho Avaliativo da Disciplina:** Computação em Nuvem — UNINTER  
> **Data de Entrega:** Julho de 2026

---

## 1. Identificação da Equipe

| Nome | RU |
| :--- | :---: |
| **Wallace Fernando Guedes da Silva** | 5146520 |
| **Pablo Patrick Machado** | 5200651 |
| **Andrey Gabriel Custódio da Silva** | 5246826 |
| **Christian Felipe de Souza Netto** | 4116816 |
| **Jessica do Nascimento Cordeiro** | 5345789 |

- **Repositório do Projeto no GitHub:** [https://github.com/wallace-pv/CloudTask-AI-SaaS.git](https://github.com/wallace-pv/CloudTask-AI-SaaS.git)
- **Curso:** Análise e Desenvolvimento de Sistemas / Computação em Nuvem — UNINTER

---

## 2. Resumo do Projeto

O **CloudTask AI SaaS** é uma aplicação cloud-native moderna desenvolvida para o gerenciamento de tarefas (SaaS de produtividade), construída utilizando **Python 3.11+ e FastAPI**. O sistema permite o cadastro e acompanhamento de tarefas (com status e prioridades), upload de arquivos anexos, disparo de eventos assíncronos e verificação de saúde da infraestrutura.

O projeto foi estruturado com foco em **Arquitetura Cloud Moderna**, evoluindo de uma API local containerizada com **Docker** e banco de dados relacional **PostgreSQL** (via SQLAlchemy) para uma infraestrutura distribuída e altamente escalável na **Amazon Web Services (AWS)** e **Kubernetes (Kind / EKS)**. A persistência de objetos é feita no **Amazon S3** (com fallback local em disco), os logs e eventos de tarefas são registrados no **Amazon DynamoDB**, e todo o provisionamento estrutural foi modelado usando **AWS CDK (Infraestrutura como Código)**.

---

## 3. O que foi implementado (Evolução por Semana)

| Semana | Tema & Entregas Focais | O que foi implementado | Evidência / Como Validar |
| :---: | :--- | :--- | :--- |
| **Semana 1** | Fundamentos Cloud + Início do SaaS | API REST funcional com FastAPI (`GET /`, `GET /health`, CRUD inicial) containerizada com **Docker** (`Dockerfile` multi-stage) e ambiente padronizado com **Dev Container**. | `curl http://localhost:8000/health`<br>*(Ver print do Swagger / terminal no Anexo)* |
| **Semana 2** | Banco de Dados & Segurança Cloud | Integração com banco relacional **PostgreSQL** via Docker Compose, persistência completa do modelo `Task`, configuração de variáveis (`.env` via Pydantic Settings) e preparação para HTTPS/TLS. | `curl http://localhost:8000/tasks`<br>*(Ver print do CRUD no banco SQL)* |
| **Semana 3** | Armazenamento Cloud & Kubernetes | Serviço de upload de arquivos (`POST /uploads`) integrado ao **Amazon S3** com URL pré-assinada e fallback local, além da orquestração em contêineres com **Kubernetes (Kind local)** via manifestos em `infra/k8s/`. | `curl -F "file=@README.md" http://localhost:8000/uploads`<br>*(Ver print dos pods `kubectl get pods`)* |
| **Semana 4** | AWS Real & Amazon EKS | Criação de repositório de imagens no **Amazon ECR**, automação de build/push via script (`build-push-ecr.sh`) e deploy da aplicação em cluster na nuvem via **Amazon EKS** com serviço `LoadBalancer`. | Acesso via DNS externo do ELB na AWS<br>*(Ver print da aplicação online na AWS)* |
| **Semana 5** | Escalabilidade, Custos & NoSQL | Configuração de autoescala com **Horizontal Pod Autoscaler (HPA)** e testes de carga (`load-test-simple.py`), controle de custos cloud e arquitetura híbrida SQL + NoSQL com envio de eventos assíncronos para o **Amazon DynamoDB** (`POST /events`). | `GET /events` retornando eventos de auditoria<br>*(Ver print de réplicas escalando)* |
| **Semana 6** | IaC (AWS CDK) & Finalização | Provisionamento automatizado de infraestrutura como código (IaC) com **AWS CDK em Python** (VPC, ECR, S3), validação de segurança/LGPD e documentação de fechamento. | `cd infra/cdk && cdk synth`<br>*(Ver diagramas e checklists finais)* |

---

## 4. Arquitetura do Sistema

A arquitetura do CloudTask AI SaaS foi desenhada seguindo os pilares do AWS Well-Architected Framework (Excelência Operacional, Segurança, Confiabilidade, Eficiência de Performance e Otimização de Custos):

```
                       [ Usuário / Cliente REST / Web ]
                                      │
                                      ▼
                      [ Amazon Route 53 / DNS (Opcional) ]
                                      │
                                      ▼
                      [ AWS Application Load Balancer ]
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
        [ Kubernetes / Amazon EKS - Pod API 1 ]  [ Pod API 2 (HPA Auto Scaling) ]
                   │                                     │
         ┌─────────┼──────────────────┬──────────────────┼─────────┐
         │         │                  │                  │         │
         ▼         ▼                  ▼                  ▼         ▼
   [ PostgreSQL ] [ Amazon S3 ] [ Amazon DynamoDB ] [ Amazon ECR ] [ CloudWatch ]
   (Dados Tarefas) (Uploads)     (Logs/Eventos)     (Imagens)      (Monitoramento)
```

### Camadas Arquiteturais:
1. **Borda & Balanceamento:** O tráfego HTTP/HTTPS chega pelo Load Balancer (ELB/ALB), que distribui as requisições entre as réplicas dos contêineres da API.
2. **Computação (Orquestração):** O Amazon EKS (ou Kind em ambiente local) gerencia os Pods rodando a imagem Docker gerada no Amazon ECR. O HPA monitora o consumo de CPU/memória e escala horizontalmente o número de réplicas conforme a demanda.
3. **Persistência Híbrida (SQL + NoSQL):**
   - **SQL (PostgreSQL / RDS):** Armazena os dados transacionais das tarefas (tabela `tasks`: ID, título, descrição, status, prioridade, prazos).
   - **NoSQL (DynamoDB):** Armazena eventos assíncronos, logs de auditoria e métricas de execução sem impactar a performance do banco relacional (`cloudtask-events`).
4. **Armazenamento de Objetos (S3):** Arquivos anexados às tarefas são salvos no Amazon S3, com URLs pré-assinadas com tempo de expiração para garantir segurança no acesso ao download.
5. **Segurança & Controle de Acesso (IAM):** Princípio do privilégio mínimo. Pods assumem roles IAM específicas (IRSA) para acessar apenas o bucket S3 e a tabela DynamoDB correspondentes.

---

## 5. Como Executar o Projeto (Guia Reprodutível)

### Pré-requisitos
- **Docker & Docker Desktop** instalados e rodando.
- **Git** instalado.
- **VS Code** com a extensão *Dev Containers* (recomendado).

### Passo a Passo (Modo Local via Docker Compose)

1. **Clonar o repositório da turma:**
   ```bash
   git clone https://github.com/wallace-pv/CloudTask-AI-SaaS.git
   cd CloudTask-AI-SaaS
   ```

2. **Subir os contêineres em segundo plano:**
   ```bash
   docker compose up -d --build
   ```

3. **Verificar se a API e o Banco de Dados estão rodando:**
   ```bash
   docker ps
   # Deve listar cloudtask-api (porta 8000) e cloudtask-db (porta 5432)
   ```

4. **Testar a saúde da API:**
   ```bash
   curl http://localhost:8000/health
   # Resposta esperada: {"status":"ok"}
   ```

5. **Acessar a Documentação Interativa (Swagger UI):**
   - Abra no navegador: [http://localhost:8000/docs](http://localhost:8000/docs)

6. **Derrubar o ambiente e limpar recursos:**
   ```bash
   docker compose down
   ```

---

## 6. Decisões Arquiteturais e Trade-offs

Durante o desenvolvimento, tomamos decisões estratégicas visando equilibrar custos, complexidade didática e performance:

- **PostgreSQL em Contêiner vs. AWS RDS Dedicado:** Em ambiente de desenvolvimento e testes de aula, optamos por rodar o PostgreSQL como serviço no `docker-compose` ou como Pod no Kubernetes (Kind), evitando o custo fixo contínuo de uma instância RDS gerenciada (~US$ 15-30/mês). Em ambiente de produção real, o RDS seria obrigatório pela alta disponibilidade e backups automatizados.
- **Armazenamento Híbrido (S3 com Fallback Local):** Implementamos o padrão *Strategy* em `s3_service.py` (`LocalStorage` e `S3Storage`). Isso permite que a equipe desenvolva e teste offline sem gastar requisições AWS ou depender de conexão à internet, alternando para o S3 apenas via variável `STORAGE_MODE=s3`.
- **Banco Híbrido SQL + NoSQL:** As tarefas transacionais exigem consistência ACID (PostgreSQL), mas logs de eventos e auditoria (`task.created`, `task.updated`) exigem altíssima velocidade de gravação e escalabilidade sem travar tabelas relacionais. O DynamoDB atendeu perfeitamente esse requisito com custo virtualmente zero na camada gratuita/sob demanda.
- **NAT Gateway Zerado no AWS CDK (`nat_gateways=0`):** No provisionamento da VPC via AWS CDK (`network_stack.py`), configuramos 0 NAT Gateways para evitar a cobrança fixa de ~$0,045/hora (~US$ 32/mês por gateway) que a AWS aplica mesmo sem tráfego, economizando o orçamento da conta.

---

## 7. Custos na Nuvem (Otimização e FinOps)

A gestão de custos foi uma premissa fundamental no projeto. Abaixo, o monitoramento e as ações de mitigação de despesas:

- **Recursos potencialmente cobráveis na AWS:**
  - **Amazon EKS (Control Plane):** US$ 0,10 / hora (cerca de US$ 72/mês se deixado ligado direto).
  - **Instâncias EC2 (Nós do EKS - t3.small / t3.medium):** Sob demanda conforme HPA.
  - **Application Load Balancer (ELB/ALB):** Cobrança por hora + LCU.
  - **Amazon ECR & S3:** Custo irrisório para os volumes de teste do projeto (< 1 GB).
- **Ação de FinOps / Sweep de Limpeza:** Após cada validação na AWS, executamos rigorosamente o protocolo de destruição para garantir **custo zero** ao final das atividades:
  ```bash
  # 1. Apagar workloads e Load Balancer no Kubernetes
  kubectl delete -k infra/k8s/aws/
  
  # 2. Destruir cluster EKS
  eksctl delete cluster --name cloudtask-eks --region us-east-1
  
  # 3. Destruir stacks do AWS CDK (se provisionadas via CDK)
  cd infra/cdk && cdk destroy --all
  ```
- **Confirmação de Limpeza:** Validamos via CLI (`aws eks list-clusters`, `aws elbv2 describe-load-balancers`, `aws ec2 describe-instances`) que nenhuma instância ou balanceador ficou órfão gerando cobrança acidental.

---

## 8. Conformidade Legal (LGPD) e Segurança Cloud

O sistema adota os princípios de *Security by Design* e privacidade de dados em conformidade com a **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)**:

- **Minimização de Dados:** O cadastro de usuários e tarefas armazena exclusivamente os dados estritamente necessários para o funcionamento do serviço, sem coletar dados sensíveis (como CPF, biometria ou dados bancários).
- **Criptografia em Trânsito e em Repouso:**
  - Em trânsito: Suporte a HTTPS/TLS via proxy ou Ingress Controller no Kubernetes.
  - Em repouso: O bucket S3 configurado via CDK (`storage_stack.py`) utiliza criptografia gerenciada do servidor (**SSE-S3** / `BucketEncryption.S3_MANAGED`) e bloqueio de acesso público ao bucket (`BlockPublicAccess.BLOCK_ALL`).
- **Sanitização de Entradas e Proteção contra Path Traversal:** No serviço de upload (`routes_uploads.py`), os nomes dos arquivos recebem sufixos únicos e são sanitizados (removendo caminhos como `../`), impedindo que agentes maliciosos sobrescrevam arquivos do sistema.
- **Checklist Detalhado:** A verificação completa dos itens de segurança e LGPD encontra-se no arquivo [`lgpd-checklist.md`](lgpd-checklist.md).

---

## 9. Dificuldades Encontradas e Aprendizados da Equipe

- **Conflito de Contêineres no Docker Compose:** Durante as transições de semana, enfrentamos erros de conflito de nomes de contêineres (`Conflict. The container name "/cloudtask-db" is already in use...`). **Solução/Aprendizado:** Entendemos o ciclo de vida dos volumes e contêineres e consolidamos o hábito de rodar `docker rm -f cloudtask-api cloudtask-db` ou `docker compose down -v` antes de subir novos builds, além de utilizar o rebuild limpo no VS Code Dev Containers.
- **Permissões IAM e IRSA no Kubernetes:** Configurar as credenciais para o Pod dentro do EKS conversar com o S3 e DynamoDB sem expor chaves estáticas (`AWS_ACCESS_KEY_ID`) no `.env` foi um desafio conceitual. **Aprendizado:** Compreendemos a força da segurança cloud moderna usando IAM Roles for Service Accounts (IRSA), where the service account temporary AWS credentials from STS.
- **Evolução de Script para IaC:** Ver a infraestrutura nascer manualmente no console, depois via shell script e finalmente ser provisionada com 10 linhas de código Python no **AWS CDK** mostrou à equipe a importância da automação, escalabilidade e versionamento de infraestrutura em ambientes cloud profissionais.

---

## 10. Anexos e Evidências Visuais

Os checklists de verificação preenchidos estão disponíveis diretamente na pasta `docs/entrega-final/`:

- [x] **Checklist de Segurança & LGPD:** [`docs/entrega-final/lgpd-checklist.md`](lgpd-checklist.md)
- [x] **Checklist de Deploy e Varredura de Custos:** [`docs/entrega-final/deployment-checklist.md`](deployment-checklist.md)

### Registro de Evidências (Prints e Comandos)

*(Para a geração do PDF final, adicione abaixo as capturas de tela obtidas rodando o projeto no VS Code e na AWS)*

#### 1. Aplicação Funcionando (FastAPI & Swagger UI)
`[ INSERIR AQUI PRINT DO NAVEGADOR EM http://localhost:8000/docs COM A API ATIVA ]`

#### 2. Contêineres Docker Ativos no Terminal
`[ INSERIR AQUI PRINT DO TERMINAL NO VS CODE MOSTRANDO A SAÍDA DO COMANDO: docker ps ]`

#### 3. Execução de CRUD de Tarefas e Upload de Arquivos
`[ INSERIR AQUI PRINT DE UMA REQUISIÇÃO POST /tasks E POST /uploads COM SUCESSO ]`

#### 4. Kubernetes Funcionando (Pods e Serviços Ativos)
`[ INSERIR AQUI PRINT DO TERMINAL MOSTRANDO: kubectl get pods -n cloudtask ]`

#### 5. Deploy na Nuvem (AWS EKS / S3 / DynamoDB)
`[ INSERIR AQUI PRINT DO CONSOLE AWS OU DO TERMINAL ACESSANDO O DNS DO LOAD BALANCER NA NUVEM ]`
