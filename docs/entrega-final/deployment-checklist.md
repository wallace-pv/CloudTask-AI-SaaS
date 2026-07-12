# Checklist de deploy + custos — CloudTask AI SaaS

Rode esta lista **antes** de demonstrar/entregar e **depois** para garantir que
nada ficou cobrando. Vale para o deploy final (EKS/RDS/ALB) ou para qualquer
demo na nuvem.

> Comandos de diagnóstico detalhados:
> [`../praticas/99-troubleshooting.md`](../praticas/99-troubleshooting.md) §💸 Custos.

---

## Antes do deploy

- [x] Credenciais AWS válidas: `aws sts get-caller-identity` retorna seu ARN.
- [x] Região correta: `aws configure get region` (`us-east-1`).
- [x] Imagem no ECR: `aws ecr list-images --repository-name cloudtask-api`.
- [x] `.env` / Secret revisados (sem placeholders tipo `USER:SENHA@HOST`).
- [x] Banco definido: RDS criado **ou** Postgres como Pod (ciente do trade-off).

## Durante (subir)

- [x] Cluster EKS pronto: `kubectl get nodes` em `Ready`.
- [x] metrics-server ok (se for usar HPA): `kubectl top nodes` lista CPU.
- [x] `kubectl apply -k infra/k8s/aws/` aplicado sem erro.
- [x] Pods `Running`: `kubectl get pods -n cloudtask`.
- [x] Serviço acessível: `curl http://<ELB>/health` → 200, `/health/ready` → db ok.

## Verificação funcional (demonstrar)

- [x] CRUD: criar/listar/atualizar/excluir tarefa (Swagger ou curl).
- [x] Upload: `POST /uploads` (local ou S3) e download.
- [x] Evento: criar tarefa gera `task.created` (`GET /events`).
- [x] (Opcional) HPA: gerar carga e ver réplicas subir/descer.

## 🔥 Depois (destruir — OBRIGATÓRIO)

> Ordem importa: **Service LoadBalancer primeiro** (libera o ELB), cluster por último.

- [x] `kubectl delete -k infra/k8s/aws/` (apaga workloads + ELB).
- [x] `eksctl delete cluster --name <cluster>` (ou Console → Delete).
- [x] RDS apagado (se criado): `aws rds delete-db-instance ... --skip-final-snapshot`.
- [x] DynamoDB apagado: `aws dynamodb delete-table --table-name cloudtask-events`.
- [x] S3 de teste apagado.
- [x] `cdk destroy --all` (se usou CDK).

## Sweep final (tudo vazio = zero cobrança)

```bash
aws eks list-clusters --region us-east-1 --query clusters --output text
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running,pending" --query "Reservations[].Instances[].InstanceId" --output text --region us-east-1
aws elbv2 describe-load-balancers --query "LoadBalancers[].DNSName" --output text --region us-east-1
aws ec2 describe-nat-gateways --filter "Name=state,Values=available,pending" --query "NatGateways[].NatGatewayId" --output text --region us-east-1
aws ec2 describe-addresses --query "Addresses[?AssociationId==null].PublicIp" --output text --region us-east-1
aws rds describe-db-instances --query "DBInstances[].DBInstanceIdentifier" --output text --region us-east-1
```

- [x] Tudo acima **vazio**.
- [x] (24h depois) Cost Explorer / Billing sem gasto inesperado.
