"""EventsStack — tabela DynamoDB de eventos/logs (Aula 11, casa com a Aula 10).

Descreve como código a mesma tabela que na Semana 5 (Aula 10) criamos com
``aws dynamodb create-table``. É o backend NoSQL dos eventos do CloudTask
(``EVENT_STORE_MODE=dynamodb``).

    * ``billing_mode=PAY_PER_REQUEST`` -> cobra só por uso (centavos na aula),
      sem capacidade reservada parada.
    * chave de partição ``id`` (String) -> como o DynamoDB localiza o evento.
    * ``removal_policy=DESTROY`` -> ``destroy`` apaga a tabela (sem órfão).

Sem assets (sem Lambda) -> sobe no Academy sem ``cdk bootstrap``.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack, CfnOutput
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class EventsStack(Stack):
    """Cria a tabela DynamoDB de eventos (PAY_PER_REQUEST)."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # POR QUÊ não fixamos `table_name`: evita colisão se a tabela já existir
        # (criada na Aula 10 pelo `aws dynamodb create-table`). O nome sai no Output.
        self.table = dynamodb.Table(
            self,
            "EventsTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        CfnOutput(
            self,
            "EventsTableName",
            value=self.table.table_name,
            description="Nome da tabela DynamoDB (use em DYNAMODB_TABLE_NAME)",
        )
