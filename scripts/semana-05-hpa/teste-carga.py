#!/usr/bin/env python3
"""Semana 5 · Aula 9 — Teste de carga simples — só com a biblioteca padrão do Python.

Dispara muitas requisições HTTP em paralelo contra um endpoint durante alguns
segundos e, ao final, imprime um resumo (total, sucesso/erro, requisições por
segundo e latência média). Serve para **ver o HPA reagir** na Aula 9: enquanto
este script roda, observe ``kubectl get hpa -n cloudtask -w`` — as réplicas
sobem quando a CPU passa do alvo.

POR QUÊ só stdlib (``urllib`` + ``threading``), sem ``requests``/``httpx``:
    o aluno roda com um ``python`` puro, sem instalar nada. Para um teste de
    carga didático isso basta. Ferramentas profissionais (k6, Locust, wrk) dão
    métricas melhores, mas fogem do escopo da disciplina.

Limitação conhecida:
    o GIL e o modelo de threads do Python limitam o throughput real. Este
    script mede "carga suficiente para acionar o HPA", não um benchmark preciso.

Exemplos:
    Carga leve por 30 s contra o /health::

        python scripts/semana-05-hpa/teste-carga.py --url http://localhost:8000/health \\
            --concurrency 20 --duration 30

    Carga mais pesada contra um ELB do EKS::

        python scripts/semana-05-hpa/teste-carga.py --url http://<elb-dns>/tasks \\
            --concurrency 50 --duration 60
"""

from __future__ import annotations

import argparse
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Stats:
    """Acumula os resultados das requisições de forma thread-safe.

    Vários workers escrevem aqui ao mesmo tempo, por isso todo acesso é
    protegido por um :class:`threading.Lock`.

    Attributes:
        ok: Quantidade de respostas com status HTTP 2xx/3xx.
        errors: Quantidade de falhas (timeout, conexão recusada, status >= 400).
        total_latency: Soma das latências (segundos) das respostas bem-sucedidas.
    """

    ok: int = 0
    errors: int = 0
    total_latency: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record_ok(self, latency: float) -> None:
        """Registra uma requisição bem-sucedida e sua latência (segundos)."""
        with self._lock:
            self.ok += 1
            self.total_latency += latency

    def record_error(self) -> None:
        """Registra uma requisição que falhou."""
        with self._lock:
            self.errors += 1

    @property
    def total(self) -> int:
        """Total de requisições (sucessos + erros)."""
        return self.ok + self.errors

    @property
    def avg_latency_ms(self) -> float:
        """Latência média das respostas OK, em milissegundos (0 se não houve OK)."""
        return (self.total_latency / self.ok * 1000) if self.ok else 0.0


def _worker(url: str, deadline: float, timeout: float, stats: Stats) -> None:
    """Faz requisições em laço até o tempo acabar (``deadline``).

    Args:
        url: Endereço alvo (ex.: ``http://localhost:8000/health``).
        deadline: Instante (``time.monotonic``) em que o worker deve parar.
        timeout: Tempo máximo (segundos) por requisição.
        stats: Objeto compartilhado onde os resultados são acumulados.
    """
    while time.monotonic() < deadline:
        start = time.monotonic()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                resp.read()  # drena o corpo para liberar a conexão
                if 200 <= resp.status < 400:
                    stats.record_ok(time.monotonic() - start)
                else:
                    stats.record_error()
        except (urllib.error.URLError, OSError, ValueError):
            # URLError cobre timeout/conexão; OSError/ValueError cobrem o resto.
            stats.record_error()


def run_load_test(url: str, concurrency: int, duration: float, timeout: float = 5.0) -> Stats:
    """Executa o teste de carga e devolve as estatísticas agregadas.

    Sobe ``concurrency`` threads que martelam ``url`` por ``duration`` segundos.

    Args:
        url: Endereço alvo.
        concurrency: Número de threads paralelas (clientes simultâneos).
        duration: Duração total do teste, em segundos.
        timeout: Tempo máximo por requisição, em segundos.

    Returns:
        Stats: contadores de sucesso/erro e latência média.
    """
    stats = Stats()
    deadline = time.monotonic() + duration
    threads = [
        threading.Thread(target=_worker, args=(url, deadline, timeout, stats), daemon=True)
        for _ in range(concurrency)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return stats


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Lê e valida os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Teste de carga simples (stdlib) para acionar o HPA.",
    )
    parser.add_argument("--url", required=True, help="Endpoint alvo, ex.: http://localhost:8000/health")
    parser.add_argument("--concurrency", type=int, default=20, help="Threads paralelas (default: 20)")
    parser.add_argument("--duration", type=float, default=30.0, help="Duração em segundos (default: 30)")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout por requisição em s (default: 5)")
    args = parser.parse_args(argv)
    if args.concurrency < 1:
        parser.error("--concurrency deve ser >= 1")
    if args.duration <= 0:
        parser.error("--duration deve ser > 0")
    return args


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: roda o teste e imprime o resumo.

    Returns:
        int: código de saída (0 sempre que o teste roda; não falha por erros HTTP,
        pois erros sob carga são esperados e fazem parte da observação).
    """
    args = _parse_args(argv)
    print(
        f"Carga: {args.concurrency} clientes x {args.duration:.0f}s contra {args.url}",
        flush=True,
    )
    started = time.monotonic()
    stats = run_load_test(args.url, args.concurrency, args.duration, args.timeout)
    elapsed = time.monotonic() - started

    rps = stats.total / elapsed if elapsed else 0.0
    print("\n--- Resultado ---")
    print(f"Total de requisições : {stats.total}")
    print(f"  OK (2xx/3xx)       : {stats.ok}")
    print(f"  Erros              : {stats.errors}")
    print(f"Tempo decorrido      : {elapsed:.1f}s")
    print(f"Requisições/segundo  : {rps:.1f}")
    print(f"Latência média (OK)  : {stats.avg_latency_ms:.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
