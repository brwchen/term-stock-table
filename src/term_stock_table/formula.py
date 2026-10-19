"""Custom Indicator Formula Scripting Engine module.
Allows users to define and evaluate custom quantitative expressions:
- Variables: OPEN, HIGH, LOW, CLOSE, VOL, AMT, PRE_CLOSE, PE, PB
- Functions: MA(series, n), EMA(series, n), STD(series, n), MAX(a, b), MIN(a, b), ABS(x)
- Dynamic calculation and extra table columns
"""

from __future__ import annotations

import ast
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from .config import DEFAULT_CONFIG_DIR

FORMULAS_FILE = DEFAULT_CONFIG_DIR / "formulas.json"


@dataclass
class CustomFormula:
    """User-defined formula specification."""
    name: str
    expression: str
    description: str = ""
    format_spec: str = "{:.2f}"


class SafeFormulaEvaluator(ast.NodeVisitor):
    """AST-based safe math and technical indicator formula evaluator."""

    ALLOWED_NODES = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd,
        ast.Load, ast.Tuple, ast.List
    )

    def __init__(self, context_vars: Dict[str, Any], price_history: Optional[List[float]] = None):
        self.context = context_vars
        self.history = price_history or []
        self.functions = {
            "MA": self._fn_ma,
            "EMA": self._fn_ema,
            "STD": self._fn_std,
            "ABS": abs,
            "MAX": max,
            "MIN": min,
            "ROUND": round,
            "SQRT": math.sqrt,
        }

    def _fn_ma(self, series: Any, window: int = 5) -> float:
        data = self._to_series(series)
        if not data:
            return 0.0
        w = max(1, min(len(data), int(window)))
        return sum(data[-w:]) / w

    def _fn_ema(self, series: Any, window: int = 12) -> float:
        data = self._to_series(series)
        if not data:
            return 0.0
        k = 2.0 / (window + 1)
        ema = data[0]
        for val in data[1:]:
            ema = val * k + ema * (1 - k)
        return ema

    def _fn_std(self, series: Any, window: int = 20) -> float:
        data = self._to_series(series)
        if len(data) < 2:
            return 0.0
        w = max(2, min(len(data), int(window)))
        subset = data[-w:]
        mean = sum(subset) / w
        var = sum((x - mean) ** 2 for x in subset) / (w - 1)
        return math.sqrt(var)

    def _to_series(self, val: Any) -> List[float]:
        if isinstance(val, list):
            return val
        if self.history:
            return self.history
        return [float(val)] if isinstance(val, (int, float)) else [100.0]

    def evaluate(self, expr_str: str) -> float:
        """Parse and evaluate math expression safely."""
        try:
            tree = ast.parse(expr_str.strip(), mode="eval")
            self._validate_ast(tree)
            return float(self.visit(tree.body))
        except Exception:
            return 0.0

    def _validate_ast(self, node: ast.AST) -> None:
        for child in ast.walk(node):
            if not isinstance(child, self.ALLOWED_NODES):
                raise ValueError(f"Disallowed AST element: {type(child).__name__}")

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Name(self, node: ast.Name) -> Any:
        var_name = node.id.upper()
        if var_name in self.context:
            return self.context[var_name]
        if var_name in self.functions:
            return self.functions[var_name]
        if var_name == "CLOSE" and self.history:
            return self.history[-1]
        return 0.0

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        return operand

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            return left / right if right != 0 else 0.0
        elif isinstance(node.op, ast.Mod):
            return left % right if right != 0 else 0.0
        elif isinstance(node.op, ast.Pow):
            return left ** right
        return 0.0

    def visit_Call(self, node: ast.Call) -> Any:
        func = self.visit(node.func)
        args = [self.visit(a) for a in node.args]
        if callable(func):
            return func(*args)
        raise ValueError(f"Uncallable target in formula")


class FormulaManager:
    """Manages persistent custom formulas and evaluation."""

    DEFAULT_FORMULAS: Dict[str, CustomFormula] = {
        "TYPICAL_PRICE": CustomFormula(
            "TYPICAL_PRICE",
            "(HIGH + LOW + CLOSE) / 3",
            "Typical Price (均价枢轴点)",
            "{:.2f}"
        ),
        "DEV_MA20_PCT": CustomFormula(
            "DEV_MA20_PCT",
            "(CLOSE - MA(CLOSE, 20)) / MA(CLOSE, 20) * 100",
            "Deviation from MA20 (%)",
            "{:+.2f}%"
        ),
        "INTRADAY_AMPLITUDE": CustomFormula(
            "INTRADAY_AMPLITUDE",
            "(HIGH - LOW) / PRE_CLOSE * 100",
            "True Intraday Amplitude (%)",
            "{:.2f}%"
        ),
    }

    @classmethod
    def load_formulas(cls) -> Dict[str, CustomFormula]:
        """Load user formulas from disk or return defaults."""
        if not FORMULAS_FILE.exists():
            return cls.DEFAULT_FORMULAS.copy()
        try:
            raw = json.loads(FORMULAS_FILE.read_text(encoding="utf-8"))
            formulas = {}
            for k, v in raw.items():
                formulas[k] = CustomFormula(**v)
            return formulas
        except Exception:
            return cls.DEFAULT_FORMULAS.copy()

    @classmethod
    def save_formula(cls, formula: CustomFormula) -> None:
        """Save new custom formula."""
        all_forms = cls.load_formulas()
        all_forms[formula.name.upper()] = formula
        serialized = {k: asdict(v) for k, v in all_forms.items()}
        FORMULAS_FILE.write_text(json.dumps(serialized, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def evaluate_tracker(cls, formula: CustomFormula, tracker: Any) -> float:
        """Evaluate formula against StockDataTracker instance."""
        ctx = {
            "OPEN": getattr(tracker, "open", tracker.price),
            "HIGH": getattr(tracker, "high", tracker.price),
            "LOW": getattr(tracker, "low", tracker.price),
            "CLOSE": getattr(tracker, "price", 100.0),
            "PRE_CLOSE": getattr(tracker, "prev_close", 100.0),
            "VOL": getattr(tracker, "volume", 1000),
            "AMT": getattr(tracker, "amount", 100000.0),
            "PE": getattr(tracker, "pe", 20.0) or 20.0,
            "PB": getattr(tracker, "pb", 3.0) or 3.0,
        }
        prices = getattr(tracker, "prices", [tracker.price] * 30)
        evaluator = SafeFormulaEvaluator(ctx, price_history=prices)
        return evaluator.evaluate(formula.expression)
