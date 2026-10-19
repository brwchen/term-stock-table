"""Boss Mode: Instant camouflage and work disguises for terminal privacy."""
import random
import time
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import SIMPLE, SQUARE, ROUNDED

PROFILES = ["devops", "kubectl", "nginx", "monochrome"]


def render_devops_top() -> Table:
    """Disguise as Linux top / htop system process monitor."""
    table = Table(
        box=SIMPLE,
        expand=True,
        show_header=True,
        header_style="bold black on grey70",
        title_style="bold green",
    )
    table.title = f"top - {time.strftime('%H:%M:%S')} up 42 days, 14:12, 2 users, load average: 1.42, 1.28, 1.15"
    table.caption = "Tasks: 312 total, 1 running, 311 sleeping, 0 stopped, 0 zombie | %Cpu(s): 4.2 us, 1.8 sy, 0.0 ni, 93.8 id"

    table.add_column("PID", justify="right", style="bold cyan", width=8)
    table.add_column("USER", justify="left", style="white", width=10)
    table.add_column("PR", justify="right", style="dim", width=4)
    table.add_column("NI", justify="right", style="dim", width=4)
    table.add_column("VIRT", justify="right", style="dim", width=10)
    table.add_column("RES", justify="right", style="dim", width=10)
    table.add_column("SHR", justify="right", style="dim", width=8)
    table.add_column("S", justify="center", style="bold green", width=4)
    table.add_column("%CPU", justify="right", style="bold green", width=8)
    table.add_column("%MEM", justify="right", style="cyan", width=8)
    table.add_column("TIME+", justify="right", style="dim", width=10)
    table.add_column("COMMAND", justify="left", style="bold white")

    fake_procs = [
        ("1042", "root", "20", "0", "4.2G", "1.2G", "24M", "S", "12.4", "3.8", "42:15.82", "/usr/bin/dockerd -H fd:// --containerd=/run/containerd.sock"),
        ("1892", "xchen", "20", "0", "8.9G", "3.4G", "128M", "S", "8.5", "10.6", "118:04.12", "java -Xms4g -Xmx8g -jar backend-gateway-service.jar"),
        ("2104", "xchen", "20", "0", "1.8G", "512M", "48M", "S", "4.2", "1.6", "14:22.05", "node dist/server.js --cluster=4 --port=8080"),
        ("2490", "postgres", "20", "0", "2.4G", "820M", "112M", "S", "3.1", "2.5", "89:45.31", "postgres: checkpointer process"),
        ("3108", "redis", "20", "0", "512M", "180M", "12M", "S", "1.5", "0.6", "08:12.40", "redis-server 0.0.0.0:6379"),
        ("3540", "xchen", "20", "0", "480M", "92M", "18M", "S", "0.8", "0.3", "02:04.19", "python3 -m celery -A worker worker --loglevel=info"),
        ("4102", "xchen", "20", "0", "320M", "64M", "14M", "R", "0.5", "0.2", "00:45.10", "top -d 1.0"),
    ]

    for p in fake_procs:
        table.add_row(*p)

    return table


def render_kubectl_pods() -> Table:
    """Disguise as Kubernetes kubectl get pods dashboard."""
    table = Table(
        box=SIMPLE,
        expand=True,
        show_header=True,
        header_style="bold black on grey70",
        title_style="bold blue",
    )
    table.title = "kubectl get pods --all-namespaces -o wide"
    table.caption = "Kubernetes Cluster: prod-k8s-us-west-2 | Context: default"

    table.add_column("NAMESPACE", justify="left", style="bold cyan", width=16)
    table.add_column("NAME", justify="left", style="white", width=34)
    table.add_column("READY", justify="center", style="bold green", width=8)
    table.add_column("STATUS", justify="left", style="bold green", width=12)
    table.add_column("RESTARTS", justify="right", style="dim", width=10)
    table.add_column("AGE", justify="right", style="dim", width=8)
    table.add_column("IP", justify="left", style="dim", width=14)
    table.add_column("NODE", justify="left", style="dim")

    fake_pods = [
        ("production", "api-gateway-7d4b9c5f6b-xk291", "2/2", "Running", "0", "4d", "10.244.1.42", "node-pool-1-a8f"),
        ("production", "order-service-6f8c7b4a2d-m9v01", "3/3", "Running", "0", "12d", "10.244.2.18", "node-pool-2-b4c"),
        ("production", "payment-service-5c9a1b8e3f-q4z82", "2/2", "Running", "1", "1d", "10.244.1.88", "node-pool-1-a8f"),
        ("ingress-nginx", "ingress-nginx-controller-8a4b2c-w1x90", "1/1", "Running", "0", "30d", "10.244.0.12", "node-ingress-0"),
        ("monitoring", "prometheus-k8s-0", "3/3", "Running", "0", "42d", "10.244.3.05", "node-pool-3-c9e"),
        ("monitoring", "grafana-76d8b94f6c-p7t23", "1/1", "Running", "0", "18d", "10.244.3.22", "node-pool-3-c9e"),
        ("database", "redis-cluster-leader-0", "1/1", "Running", "0", "60d", "10.244.4.10", "node-storage-0"),
    ]

    for pod in fake_pods:
        table.add_row(*pod)

    return table


def render_nginx_logs() -> Panel:
    """Disguise as real-time Nginx web access logs."""
    text = Text()
    now_ts = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
    
    logs = [
        f'192.168.1.104 - - [{now_ts}] "GET /api/v2/metrics/health HTTP/1.1" 200 482 "-" "Prometheus/2.45.0"',
        f'10.0.4.18 - - [{now_ts}] "POST /api/v1/checkout/orders HTTP/1.1" 201 1240 "https://app.corp.internal" "Mozilla/5.0"',
        f'172.16.2.88 - - [{now_ts}] "GET /api/v1/users/me/profile HTTP/1.1" 200 892 "https://app.corp.internal" "Mozilla/5.0"',
        f'192.168.1.104 - - [{now_ts}] "GET /actuator/prometheus HTTP/1.1" 200 8912 "-" "Prometheus/2.45.0"',
        f'10.0.2.14 - - [{now_ts}] "GET /static/bundles/app.min.js HTTP/1.1" 304 0 "https://app.corp.internal" "Mozilla/5.0"',
        f'10.0.3.50 - - [{now_ts}] "POST /api/v2/auth/token/refresh HTTP/1.1" 200 256 "-" "Go-http-client/1.1"',
        f'172.16.1.12 - - [{now_ts}] "GET /healthz HTTP/1.1" 200 2 "-" "kube-probe/1.28"',
    ]

    for l in logs:
        text.append(l + "\n", style="dim white")

    return Panel(
        text,
        title="tail -f /var/log/nginx/access.log",
        title_align="left",
        box=ROUNDED,
        style="dim grey70",
    )


def render_monochrome_table(trackers) -> Table:
    """Monochrome mode: Neutral grayscale table concealing market colors."""
    table = Table(
        box=SIMPLE,
        expand=True,
        show_header=True,
        header_style="bold grey70",
        title="Telemetry Data Monitor (Stream #04)",
        caption="Press [b] to toggle normal view",
    )
    table.add_column("Sensor ID", justify="center", style="dim", width=10)
    table.add_column("Channel", justify="left", style="white", width=14)
    table.add_column("Value (ms)", justify="right", style="white", width=12)
    table.add_column("Delta (%)", justify="right", style="dim", width=12)
    table.add_column("Samples", justify="right", style="dim", width=12)
    table.add_column("Load", justify="right", style="dim", width=10)

    for tr in trackers:
        table.add_row(
            f"DEV-{tr.symbol}",
            f"chan_{tr.symbol.lower()}",
            f"{tr.price:.2f}",
            f"{tr.change_pct:+.2f}%",
            f"{tr.volume:,}",
            f"{tr.turnover_rate:.2f}",
        )
    return table


def render_boss_view(profile: str = "devops", trackers=None):
    """Render selected boss mode camouflage profile."""
    p = profile.lower()
    if p == "devops":
        return render_devops_top()
    elif p == "kubectl":
        return render_kubectl_pods()
    elif p == "nginx":
        return render_nginx_logs()
    elif p == "monochrome" and trackers:
        return render_monochrome_table(trackers)
    return render_devops_top()
