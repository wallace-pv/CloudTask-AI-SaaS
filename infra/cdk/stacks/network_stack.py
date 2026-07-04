"""NetworkStack — VPC básica (Aula 11, OPCIONAL).

Descreve, como código, uma VPC parecida com a que o ``eksctl`` cria sozinho
(Semana 4) e com a que estudamos em ``docs/conceitos/aws-networking.md``: duas
zonas de disponibilidade, com subnets **públicas** e **privadas**.

⚠️ CUSTO — LEIA ANTES DE `cdk deploy`:
    o item caro de uma VPC é o **NAT Gateway** (~US$0,045/h cada, 24/7 — cobra
    mesmo parado). Aqui usamos ``nat_gateways=0`` por padrão: as subnets
    privadas ficam **isoladas** (sem saída para a internet), o que é suficiente
    para DEMONSTRAR a topologia sem gerar custo de NAT. Se você REALMENTE
    precisar de saída a partir das subnets privadas (ex.: puxar imagem de fora),
    suba para ``nat_gateways=1`` ciente do custo — e destrua depois.

POR QUÊ esta stack é "opcional": as outras semanas não dependem desta VPC (o
EKS cria a sua própria via eksctl). Ela existe para o aluno VER a rede como
código. Você pode nem implantá-la (`cdk deploy CloudTaskStorage CloudTaskEcr`
implanta só as outras duas).
"""

from __future__ import annotations

from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkStack(Stack):
    """Cria uma VPC com subnets pública e privada em 2 AZs (sem NAT por padrão)."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "CloudTaskVpc",
            max_azs=2,           # alta disponibilidade em 2 zonas
            nat_gateways=0,      # ⚠️ 0 = sem custo de NAT (ver aviso no topo)
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    # PRIVATE_ISOLATED: sem rota para a internet (sem NAT).
                    # Trocaria para PRIVATE_WITH_EGRESS se nat_gateways>=1.
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        CfnOutput(
            self,
            "VpcId",
            value=self.vpc.vpc_id,
            description="ID da VPC criada pelo CDK",
        )
