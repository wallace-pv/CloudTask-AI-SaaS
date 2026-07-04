"""Pacote das stacks (pilhas) CDK do CloudTask AI SaaS.

Cada módulo aqui define uma :class:`aws_cdk.Stack` pequena e independente:

* :mod:`stacks.storage_stack` — bucket S3 para uploads.
* :mod:`stacks.ecr_stack`     — repositório ECR da imagem da API.
* :mod:`stacks.network_stack` — VPC básica (opcional, com aviso de custo).
"""
