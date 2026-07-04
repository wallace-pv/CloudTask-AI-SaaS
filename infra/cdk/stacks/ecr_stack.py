"""EcrStack — repositório ECR da imagem da API (Aula 11).

Descreve, como código, o mesmo repositório que na Semana 4 (Aula 7) criamos com
``aws ecr create-repository`` / pelo script. Aqui ele já vem com:

    * ``image_scan_on_push`` -> a AWS escaneia vulnerabilidades a cada push.
    * **lifecycle rule**     -> mantém só as N imagens mais recentes (evita o
      repositório crescer para sempre e acumular custo de armazenamento).
    * ``removal_policy=DESTROY`` -> DIDÁTICO: ``cdk destroy`` apaga o repositório.

POR QUÊ NÃO usamos ``empty_on_delete=True``: como no bucket S3 (ver
``storage_stack.py``), isso criaria um asset/custom resource que exigiria
``cdk bootstrap`` — bloqueado no AWS Academy. Mantemos a stack **sem assets**.
Se o repositório tiver imagens, esvazie antes do destroy:
``aws ecr batch-delete-image`` ou apague pelo Console.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack, CfnOutput, Duration
from aws_cdk import aws_ecr as ecr
from constructs import Construct


class EcrStack(Stack):
    """Cria o repositório ECR ``cloudtask-api`` com scan e lifecycle."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # POR QUÊ não fixamos `repository_name`: um nome fixo (ex.: "cloudtask-api")
        # COLIDE se o repositório já existir na conta (criado nas semanas
        # anteriores pelo deploy manual) — o CloudFormation falha com
        # "ResourceExistenceCheck". Deixar o CDK gerar o nome garante que a stack
        # sobe sempre, sem conflito. A URI final sai no Output abaixo.
        repo = ecr.Repository(
            self,
            "ApiRepository",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                # Mantém apenas as 10 imagens mais recentes. As demais são
                # expiradas automaticamente. POR QUÊ: cada push gera uma imagem
                # nova; sem isso o repositório acumularia dezenas de versões
                # antigas, todas cobrando armazenamento.
                ecr.LifecycleRule(
                    description="Manter apenas as 10 imagens mais recentes",
                    max_image_count=10,
                ),
            ],
        )

        CfnOutput(
            self,
            "ApiRepositoryUri",
            value=repo.repository_uri,
            description="URI do repositório ECR (use no docker tag/push e no Deployment)",
        )
