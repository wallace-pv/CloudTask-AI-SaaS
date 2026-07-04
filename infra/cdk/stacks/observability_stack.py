"""ObservabilityStack — CloudWatch + SNS (Aula 11).

Mostra **observabilidade como código**: onde os logs ficam, um canal de
**alerta** (SNS), um **alarme** que dispara o alerta e um **dashboard** visual.

Recursos (todos "puros", sem assets -> sobem no Academy sem bootstrap):
    * **Log Group** ``/cloudtask/app`` — destino de logs da aplicação (retém 1 semana).
    * **SNS Topic** — canal de alerta (e-mail/SMS poderiam assinar depois).
    * **Alarm** — vigia a tabela DynamoDB de eventos: se houver **requisições
      limitadas (throttling)**, dispara -> publica no SNS. Mostra a ideia de
      "monitorar + reagir".
    * **Dashboard** — um painel com a capacidade consumida da tabela + um texto
      de contexto. É o "wow" visual da aula.

DEPENDÊNCIA: recebe a tabela da :class:`EventsStack` (referência entre stacks).
Por isso a ``EventsStack`` precisa subir ANTES desta (o script cuida da ordem).
"""

from __future__ import annotations

from aws_cdk import Duration, RemovalPolicy, Stack, CfnOutput
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class ObservabilityStack(Stack):
    """Log Group + SNS + Alarme + Dashboard sobre a tabela de eventos."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        events_table: dynamodb.Table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Log Group da aplicação --------------------------------------
        log_group = logs.LogGroup(
            self,
            "AppLogGroup",
            log_group_name="/cloudtask/app",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # --- Canal de alerta (SNS) ---------------------------------------
        alerts = sns.Topic(self, "AlertsTopic", display_name="CloudTask Alerts")

        # --- Alarme: throttling de gravação na tabela de eventos ---------
        # POR QUÊ throttling de PutItem: se a tabela começa a limitar GRAVAÇÕES,
        # é sinal de carga acima do esperado — exatamente o tipo de coisa que se
        # quer saber. Usamos UMA operação (PutItem) porque um alarme só aceita
        # uma métrica simples (a agregação de TODAS as operações vira uma
        # "math expression" com >10 métricas, que o alarme rejeita).
        throttle_metric = events_table.metric_throttled_requests_for_operation(
            "PutItem",
            period=Duration.minutes(1),
        )
        alarm = cw.Alarm(
            self,
            "EventsThrottleAlarm",
            metric=throttle_metric,
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Gravações limitadas (throttling) na tabela de eventos",
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        alarm.add_alarm_action(cw_actions.SnsAction(alerts))

        # --- Dashboard visual --------------------------------------------
        dashboard = cw.Dashboard(
            self,
            "CloudTaskDashboard",
            dashboard_name="CloudTask",
        )
        dashboard.add_widgets(
            cw.TextWidget(
                markdown=(
                    "# CloudTask AI SaaS — Observabilidade\n"
                    "Painel criado por **AWS CDK** (IaC). "
                    "Mostra a tabela de eventos (DynamoDB) e o alarme de throttling."
                ),
                width=24,
                height=3,
            ),
            cw.GraphWidget(
                title="DynamoDB — capacidade consumida (eventos)",
                left=[
                    events_table.metric_consumed_read_capacity_units(),
                    events_table.metric_consumed_write_capacity_units(),
                ],
                width=12,
            ),
            cw.AlarmWidget(title="Alarme de throttling", alarm=alarm, width=12),
        )

        CfnOutput(self, "AlertsTopicArn", value=alerts.topic_arn)
        CfnOutput(self, "LogGroupName", value=log_group.log_group_name)
