"""Boss Mode: Instant camouflage and work disguises for terminal privacy."""
import random
import time
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import SIMPLE, SQUARE, ROUNDED

PROFILES = ["ops", "devops", "kubectl", "nginx", "cpp", "git", "python", "neovim", "gdb", "monochrome"]


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


def render_cpp_build() -> Panel:
    """Disguise as CMake / C++ compilation build output."""
    text = Text()
    lines = [
        "[ 42%] Building CXX object src/core/CMakeFiles/core.dir/memory_allocator.cpp.o",
        "[ 48%] Building CXX object src/core/CMakeFiles/core.dir/thread_pool.cpp.o",
        "[ 54%] Building CXX object src/engine/CMakeFiles/engine.dir/render_pipeline.cpp.o",
        "[ 61%] Building CXX object src/engine/CMakeFiles/engine.dir/shader_compiler.cpp.o",
        "[ 68%] Building CXX object src/net/CMakeFiles/net.dir/async_socket.cpp.o",
        "[ 75%] Building CXX object src/net/CMakeFiles/net.dir/tls_session.cpp.o",
        "[ 82%] Linking CXX static library libcore.a",
        "[ 88%] Linking CXX shared library libengine.dylib",
        "[ 94%] Building CXX object src/main/CMakeFiles/app.dir/main.cpp.o",
        "[100%] Linking CXX executable bin/distributed_coordinator",
        "Built target distributed_coordinator [Success: 0 warnings, 0 errors]",
    ]
    for l in lines:
        if "100%" in l or "Success" in l:
            text.append(l + "\n", style="bold green")
        elif "Building" in l:
            text.append(l + "\n", style="dim white")
        else:
            text.append(l + "\n", style="cyan")

    return Panel(
        text,
        title="ninja -C build/release -j 12 (Target: distributed_coordinator)",
        title_align="left",
        box=ROUNDED,
        style="dim grey70",
    )


def render_git_diff() -> Panel:
    """Disguise as git diff and code review output."""
    text = Text()
    diff_lines = [
        "diff --git a/src/auth/session.go b/src/auth/session.go",
        "index 8a3f12b..4e9c701 100644",
        "--- a/src/auth/session.go",
        "+++ b/src/auth/session.go",
        "@@ -142,8 +142,12 @@ func (s *SessionManager) ValidateToken(token string) (*Claims, error) {",
        " \tif claims.ExpiresAt < time.Now().Unix() {",
        "-\t\treturn nil, ErrTokenExpired",
        "+\t\tlog.Warn(\"token expired\", zap.String(\"sub\", claims.Subject))",
        "+\t\treturn nil, fmt.Errorf(\"%w: timestamp=%d\", ErrTokenExpired, claims.ExpiresAt)",
        " \t}",
        "+",
        "+\t// Verify cryptographic signature with rotation key",
        "+\tif err := s.keyRing.VerifySignature(token, claims); err != nil {",
        "+\t\treturn nil, fmt.Errorf(\"signature verification failed: %w\", err)",
        "+\t}",
        " \treturn claims, nil",
        " }",
    ]
    for dl in diff_lines:
        if dl.startswith("+") and not dl.startswith("+++"):
            text.append(dl + "\n", style="green")
        elif dl.startswith("-") and not dl.startswith("---"):
            text.append(dl + "\n", style="red")
        elif dl.startswith("@@"):
            text.append(dl + "\n", style="cyan")
        elif dl.startswith("diff") or dl.startswith("index"):
            text.append(dl + "\n", style="bold white")
        else:
            text.append(dl + "\n", style="dim white")

    return Panel(
        text,
        title="git diff HEAD~1..HEAD (feat: security token rotation)",
        title_align="left",
        box=ROUNDED,
        style="dim grey70",
    )


def render_python_train() -> Panel:
    """Disguise as PyTorch Deep Learning training loss loop."""
    text = Text()
    now_ts = time.strftime("%H:%M:%S")
    train_lines = [
        f"[{now_ts}] [INFO] Initializing TransformerBackbone(num_layers=24, heads=16, d_model=1024)",
        f"[{now_ts}] Epoch [18/50] Iter [1400/4200] lr: 1.45e-4 | Loss: 0.2842 | Perplexity: 1.328 | GradNorm: 0.84",
        f"[{now_ts}] Epoch [18/50] Iter [1600/4200] lr: 1.44e-4 | Loss: 0.2790 | Perplexity: 1.321 | GradNorm: 0.79",
        f"[{now_ts}] Epoch [18/50] Iter [1800/4200] lr: 1.42e-4 | Loss: 0.2715 | Perplexity: 1.312 | GradNorm: 0.81",
        f"[{now_ts}] Epoch [18/50] Iter [2000/4200] lr: 1.40e-4 | Loss: 0.2680 | Perplexity: 1.307 | GradNorm: 0.76",
        f"[{now_ts}] [EVAL] Val Loss: 0.2910 | Top-1 Accuracy: 94.82% | BLEU-4: 41.25",
        f"[{now_ts}] [CHECKPOINT] Best model saved to checkpoints/model_epoch18_val948.pt",
    ]
    for tl in train_lines:
        if "[CHECKPOINT]" in tl:
            text.append(tl + "\n", style="bold green")
        elif "[EVAL]" in tl:
            text.append(tl + "\n", style="bold yellow")
        else:
            text.append(tl + "\n", style="dim white")

    return Panel(
        text,
        title="python3 train_distributed.py --world_size=8 --dataset=fin_corpus",
        title_align="left",
        box=ROUNDED,
        style="dim grey70",
    )


def render_neovim_buffer() -> Panel:
    """Disguise as Neovim editing asynchronous distributed consensus code."""
    text = Text()
    lines = [
        "  1 │ use tokio::sync::{mpsc, RwLock};",
        "  2 │ use std::sync::Arc;",
        "  3 │ ",
        "  4 │ pub struct RaftEngine<State> {",
        "  5 │     node_id: u64,",
        "  6 │     current_term: Arc<RwLock<u64>>,",
        "  7 │     voted_for: Option<u64>,",
        "  8 │     log_entries: Vec<LogEntry<State>>,",
        "  9 │     tx_heartbeat: mpsc::Sender<HeartbeatPacket>,",
        " 10 │ }",
        " 11 │ ",
        " 12 │ impl<State: Clone + Send + Sync> RaftEngine<State> {",
        " 13 │     pub async fn append_entries(&mut self, term: u64, leader_id: u64) -> Result<bool, RaftError> {",
        " 14 │         let mut cur_term = self.current_term.write().await;",
        " 15 │         if term > *cur_term {",
        " 16 │             *cur_term = term;",
        " 17 │             self.voted_for = Some(leader_id);",
        " 18 │             return Ok(true);",
        " 19 │         }",
        " 20 │         Ok(false)",
        " 21 │     }",
        " 22 │ }",
        " ~  │ ",
        " NORMAL  src/consensus/raft.rs  utf-8  88%  16:24  rust-analyzer: ok",
    ]
    for l in lines:
        if "NORMAL" in l:
            text.append(l + "\n", style="bold black on bright_cyan")
        elif "pub" in l or "async" in l or "fn" in l or "impl" in l or "struct" in l:
            text.append(l + "\n", style="bold magenta")
        elif "Result" in l or "Option" in l or "Arc" in l:
            text.append(l + "\n", style="bold yellow")
        else:
            text.append(l + "\n", style="dim white")

    return Panel(
        text,
        title="NVIM v0.10.2 - src/consensus/raft.rs [Modified]",
        title_align="left",
        box=ROUNDED,
        style="dim grey70",
    )


def render_gdb_debugger() -> Panel:
    """Disguise as interactive GDB / LLDB debugger session."""
    text = Text()
    lines = [
        "(gdb) target remote localhost:3333",
        "Remote debugging using localhost:3333",
        "0x00007fff842109ab in epoll_wait () from /lib/x86_64-linux-gnu/libc.so.6",
        "(gdb) break net_core::dispatch_packet",
        "Breakpoint 1 at 0x55555558e420: file src/net/dispatcher.cpp, line 142.",
        "(gdb) continue",
        "Continuing.",
        "[Switching to Thread 0x7fff7f7fe700 (LWP 48201)]",
        "Thread 4 \"worker-4\" hit Breakpoint 1, net_core::dispatch_packet (header=0x7fff7f7fddc0, len=1420)",
        "    at src/net/dispatcher.cpp:142",
        "142         if (!verify_checksum(header->crc32, header->payload, len)) {",
        "(gdb) print *header",
        "$1 = {magic = 0x5a4f5241, version = 2, seq_id = 918402, crc32 = 0x8f2d91ab}",
        "(gdb) bt 3",
        "#0  net_core::dispatch_packet (header=0x7fff7f7fddc0, len=1420) at src/net/dispatcher.cpp:142",
        "#1  0x000055555558f120 in net_core::io_worker_loop (ctx=0x5555557b2010) at src/net/worker.cpp:89",
        "#2  0x00007fff842016ba in start_thread (arg=0x7fff7f7fe700) at pthread_create.c:481",
        "(gdb) _",
    ]
    for l in lines:
        if l.startswith("(gdb)"):
            text.append(l + "\n", style="bold green")
        elif "Breakpoint" in l or "hit" in l:
            text.append(l + "\n", style="bold yellow")
        elif l.startswith("$1") or l.startswith("#"):
            text.append(l + "\n", style="cyan")
        else:
            text.append(l + "\n", style="dim white")

    return Panel(
        text,
        title="GNU gdb (Ubuntu 12.1-0ubuntu1~22.04.2) - PID 48198",
        title_align="left",
        box=ROUNDED,
        style="dim grey70",
    )


def render_boss_view(profile: str = "devops", trackers=None):
    """Render selected boss mode camouflage profile."""
    p = profile.lower()
    if p == "ops" and trackers:
        from .stealth import render_log_view
        return render_log_view(trackers)
    if p == "devops":
        return render_devops_top()
    elif p == "kubectl":
        return render_kubectl_pods()
    elif p == "nginx":
        return render_nginx_logs()
    elif p == "cpp":
        return render_cpp_build()
    elif p == "git":
        return render_git_diff()
    elif p == "python":
        return render_python_train()
    elif p == "neovim":
        return render_neovim_buffer()
    elif p == "gdb":
        return render_gdb_debugger()
    elif p == "monochrome" and trackers:
        return render_monochrome_table(trackers)
    return render_devops_top()


def export_daily_review(
    trackers,
    notes: Optional[dict] = None,
    portfolio: Optional[dict] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate and export a comprehensive daily review markdown report.
    """
    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# 📈 Daily Financial Review & Trading Journal",
        f"> Generated on {now_str} via `term-stock-table`\n",
        "## 1. Watchlist Overview\n",
        "| Symbol | Name | Price | Change% | Change | Volume | Amount | P/E |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    
    for tr in trackers:
        sign = "+" if tr.change >= 0 else ""
        lines.append(
            f"| `{tr.symbol}` | {tr.name} | {tr.price:.2f} | {sign}{tr.change_pct:.2f}% | {sign}{tr.change:.2f} | {tr.volume:,} | {tr.amount:.1f}万 | {tr.pe or '-'} |"
        )
        
    if portfolio:
        lines.extend([
            "\n## 2. Portfolio Valuation Summary\n",
            "| Symbol | Shares | Cost Price | Current Price | Float PnL | Return% |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for sym, pos in portfolio.items():
            cost = pos.get("cost", 0)
            shares = pos.get("shares", 0)
            cur = cost
            for tr in trackers:
                if tr.symbol.upper() == sym.upper():
                    cur = tr.price
                    break
            pnl = (cur - cost) * shares
            ret_pct = ((cur - cost) / cost * 100.0) if cost > 0 else 0.0
            pnl_sign = "+" if pnl >= 0 else ""
            lines.append(
                f"| `{sym}` | {shares:,.0f} | {cost:.2f} | {cur:.2f} | {pnl_sign}{pnl:,.2f} | {pnl_sign}{ret_pct:.2f}% |"
            )
            
    if notes:
        lines.extend(["\n## 3. Investment Notes & Strategy Log\n"])
        for sym, note_list in notes.items():
            if not note_list:
                continue
            lines.append(f"### `{sym}` Notes")
            for n in note_list[:5]:
                lines.append(f"- **[{n.get('timestamp', '')}]**: {n.get('text', '')}")
            lines.append("")
            
    content = "\n".join(lines)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    return content

