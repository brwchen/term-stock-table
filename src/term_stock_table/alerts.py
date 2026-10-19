"""Price and volatility alerts evaluation and notification engine."""
import subprocess
import sys
import platform
from typing import Dict, List, Any, Optional

from .config import load_alerts, save_alert, remove_alert


def send_desktop_notification(title: str, message: str) -> None:
    """Send a non-blocking desktop notification (macOS osascript or terminal bell)."""
    system = platform.system().lower()
    if system == "darwin":
        try:
            # Clean single/double quotes to prevent shell injection
            safe_title = title.replace('"', '\\"').replace("'", "\\'")
            safe_msg = message.replace('"', '\\"').replace("'", "\\'")
            cmd = f'display notification "{safe_msg}" with title "{safe_title}"'
            subprocess.run(["osascript", "-e", cmd], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
        # Fallback terminal beep
        sys.stdout.write("\a")
        sys.stdout.flush()


def evaluate_alerts(
    quotes: List[Dict[str, Any]],
    alerts: Optional[Dict[str, Dict[str, Any]]] = None,
    trigger_notification: bool = True,
) -> Dict[str, List[str]]:
    """
    Check stock quotes against configured alert thresholds.
    Returns a mapping of symbol -> list of triggered alert message strings.
    """
    if alerts is None:
        alerts = load_alerts()
    
    triggered_map: Dict[str, List[str]] = {}
    
    for q in quotes:
        sym = q.get("symbol", "").upper()
        if sym not in alerts:
            continue
        
        cfg = alerts[sym]
        if not cfg.get("enabled", True):
            continue
        
        price = float(q.get("price", 0.0))
        change_pct = float(q.get("change_pct", 0.0))
        name = q.get("name", sym)
        
        reasons = []
        
        target_high = cfg.get("target_high")
        if target_high is not None and price >= float(target_high):
            reasons.append(f"Price reached High Target (≥ {target_high:.2f}, Cur: {price:.2f})")
            
        target_low = cfg.get("target_low")
        if target_low is not None and price <= float(target_low):
            reasons.append(f"Price hit Low Stop (≤ {target_low:.2f}, Cur: {price:.2f})")
            
        max_change_pct = cfg.get("max_change_pct")
        if max_change_pct is not None and abs(change_pct) >= float(max_change_pct):
            reasons.append(f"Volatility exceeded ±{max_change_pct:.1f}% (Cur: {change_pct:+.2f}%)")
            
        if reasons:
            triggered_map[sym] = reasons
            if trigger_notification:
                notif_msg = f"{name} ({sym}): " + " | ".join(reasons)
                send_desktop_notification(f"🚨 Stock Alert: {sym}", notif_msg)
                
    return triggered_map
