import ast
import re
from pathlib import Path


class StrategyASTAnalyzer:

    def __init__(self, strategy_file):
        self.strategy_file = Path(strategy_file)

    def analyze(self):

        if not self.strategy_file.exists():
            return {
                "status": "failed",
                "reason": "strategy file missing"
            }

        text = self.strategy_file.read_text(errors="ignore")

        tree = ast.parse(text)

        result = {
            "buy_conditions": [],
            "sell_conditions": [],
            "score_rules": [],
            "recommendations": [],
            "risk_level": "unknown"
        }

        for node in ast.walk(tree):

            if isinstance(node, ast.If):

                cond = ast.unparse(node.test)

                if any(
                    x in cond.lower()
                    for x in [
                        "price_change",
                        "volume",
                        "liquidity",
                        "age",
                        "mint",
                        "balance",
                        "daily_pnl",
                        "positions"
                    ]
                ):
                    result["buy_conditions"].append(cond)

                if any(
                    x in cond.lower()
                    for x in [
                        "stop_loss",
                        "take_profit",
                        "held_min",
                        "should_sell",
                        "current_price"
                    ]
                ):
                    result["sell_conditions"].append(cond)

        result["score_rules"] = extract_score_rules(
            tree
        )

        result["duplicate_conditions"] = (
            detect_duplicate_conditions(
                result["buy_conditions"]
            )
        )

        text_lower = text.lower()

        if "marketcap" not in text_lower:
            result["recommendations"].append(
                "missing marketcap filter"
            )

        if "holder" not in text_lower:
            result["recommendations"].append(
                "missing holder distribution check"
            )

        if "liquidity > 50000" in text_lower:
            result["recommendations"].append(
                "review liquidity threshold"
            )

        risk_score = 0

        if "marketcap" not in text_lower:
            risk_score += 1

        if "holder" not in text_lower:
            risk_score += 1

        if risk_score == 0:
            result["risk_level"] = "low"
        elif risk_score == 1:
            result["risk_level"] = "medium"
        else:
            result["risk_level"] = "high"

        result["buy_conditions"] = list(
            dict.fromkeys(result["buy_conditions"])
        )

        result["sell_conditions"] = list(
            dict.fromkeys(result["sell_conditions"])
        )



        result["overlapping_rules"] = (
            detect_overlapping_rules(
                result["score_rules"]
            )
        )

        result["dead_conditions"] = (
            detect_dead_conditions(
                result["buy_conditions"]
            )
        )

        risk = estimate_risk_score(
            result
        )

        result.update(risk)

        result["strategy_report"] = (
            generate_strategy_report(
                result
            )
        )

        result["optimization_tasks"] = (
            generate_optimization_tasks(
                result
            )
        )

        result["unreachable_branches"] = (
            detect_unreachable_branches(
                result["score_rules"]
            )
        )

        result["impossible_conditions"] = (
            detect_impossible_conditions(
                result["buy_conditions"]
            )
        )

        result["conflicting_filters"] = (
            detect_conflicting_filters(
                result["buy_conditions"]
            )
        )

        rr = extract_strategy_rr(
            self.strategy_file
        )

        result["rr_source"] = rr

        result["rr_ratio"] = (
            estimate_rr_ratio(result)
        )

        result["expected_winrate"] = (
            estimate_expected_winrate(
                result
            )
        )

        result["quality_score"] = (
            strategy_quality_score(
                result
            )
        )

        result["patch_suggestions"] = (
            generate_patch_suggestions(
                result
            )
        )

        result["safe_refactor_plan"] = (
            generate_safe_refactor_plan(
                result
            )
        )

        enqueue_optimization_tasks(
            result[
                "optimization_tasks"
            ]
        )


        return result


def extract_score_rules(tree):
    import ast

    rules = []

    class V(ast.NodeVisitor):
        def visit_If(self, node):
            cond = ast.unparse(node.test)

            for stmt in node.body:
                if (
                    isinstance(stmt, ast.AugAssign)
                    and isinstance(stmt.target, ast.Name)
                    and stmt.target.id == "score"
                    and isinstance(stmt.op, ast.Add)
                ):
                    try:
                        score = int(ast.unparse(stmt.value))
                    except Exception:
                        score = ast.unparse(stmt.value)

                    rules.append({
                        "condition": cond,
                        "score": score
                    })

            self.generic_visit(node)

    V().visit(tree)
    return rules


def detect_duplicate_conditions(conditions):
    seen = set()
    dup = []

    for c in conditions:
        if c in seen and c not in dup:
            dup.append(c)
        seen.add(c)

    return dup



def detect_overlapping_rules(score_rules):

    import re

    overlaps = []

    def parse_condition(cond):

        m = re.search(
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([<>]=?)\s*(-?\d+\.?\d*)',
            cond
        )

        if not m:
            return None

        return {
            "field": m.group(1),
            "op": m.group(2),
            "value": float(m.group(3))
        }

    for i, a in enumerate(score_rules):

        pa = parse_condition(
            str(a["condition"])
        )

        if not pa:
            continue

        for b in score_rules[i + 1:]:

            pb = parse_condition(
                str(b["condition"])
            )

            if not pb:
                continue

            if pa["field"] != pb["field"]:
                continue

            overlap = False

            if (
                pa["op"].startswith(">")
                and pb["op"].startswith(">")
            ):
                overlap = True

            elif (
                pa["op"].startswith("<")
                and pb["op"].startswith("<")
            ):
                overlap = True

            if overlap:
                overlaps.append({
                    "field": pa["field"],
                    "rule1": a["condition"],
                    "rule2": b["condition"]
                })

    return overlaps


def detect_dead_conditions(buy_conditions):

    import re

    dead = []

    parsed = []

    for cond in buy_conditions:

        m = re.search(
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*([<>]=?)\s*(-?\d+\.?\d*)',
            cond
        )

        if not m:
            continue

        parsed.append({
            "condition": cond,
            "field": m.group(1),
            "op": m.group(2),
            "value": float(m.group(3))
        })

    for a in parsed:

        for b in parsed:

            if a is b:
                continue

            if a["field"] != b["field"]:
                continue

            if (
                a["op"].startswith(">")
                and b["op"].startswith(">")
                and a["value"] > b["value"]
            ):
                dead.append({
                    "condition": b["condition"],
                    "shadowed_by": a["condition"]
                })

            elif (
                a["op"].startswith("<")
                and b["op"].startswith("<")
                and a["value"] < b["value"]
            ):
                dead.append({
                    "condition": b["condition"],
                    "shadowed_by": a["condition"]
                })

    unique = []

    for x in dead:
        if x not in unique:
            unique.append(x)

    return unique

def estimate_risk_score(result):
    score = 0

    if len(result["buy_conditions"]) < 5:
        score += 20

    if not result["score_rules"]:
        score += 20

    if "missing holder distribution check" in result["recommendations"]:
        score += 20

    if "review liquidity threshold" in result["recommendations"]:
        score += 10

    if score >= 60:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"

    return {
        "risk_score": score,
        "risk_level": level
    }


def generate_strategy_report(result):
    return {
        "buy_filters": len(result["buy_conditions"]),
        "sell_filters": len(result["sell_conditions"]),
        "score_rules": len(result["score_rules"]),
        "duplicates": len(result["duplicate_conditions"]),
        "overlaps": len(result["overlapping_rules"]),
        "risk": result["risk_score"]
    }


def generate_optimization_tasks(result):

    tasks = []

    txt = " ".join(
        result.get(
            "buy_conditions",
            []
        )
    ).lower()

    if "holder" not in txt:
        tasks.append(
            "Add holder concentration filter"
        )

    if "liquidity > 50000" in txt:
        tasks.append(
            "Review liquidity threshold"
        )

    if result.get(
        "overlapping_rules"
    ):
        tasks.append(
            "Review overlapping score rules"
        )

    for dead in result.get(
        "dead_conditions",
        []
    ):
        tasks.append(
            f"Remove dead condition: {dead['condition']}"
        )

    if result.get(
        "risk_score",
        0
    ) >= 30:
        tasks.append(
            "Reduce strategy risk score"
        )

    return list(
        dict.fromkeys(tasks)
    )


def generate_safe_refactor_plan(result):

    plan = []

    for dead in result.get(
        "dead_conditions",
        []
    ):
        plan.append({
            "action":
                "remove_dead_condition",
            "target":
                dead["condition"],
            "reason":
                f"shadowed by {dead['shadowed_by']}"
        })

    for overlap in result.get(
        "overlapping_rules",
        []
    ):
        plan.append({
            "action":
                "merge_overlap",
            "field":
                overlap["field"],
            "rule1":
                overlap["rule1"],
            "rule2":
                overlap["rule2"]
        })

    txt = " ".join(
        result.get(
            "buy_conditions",
            []
        )
    ).lower()

    if "holder" not in txt:
        plan.append({
            "action":
                "add_filter",
            "target":
                "holder_concentration"
        })

    if "mint_authority" not in txt:
        plan.append({
            "action":
                "add_filter",
            "target":
                "mint_authority_check"
        })

    if "freeze_authority" not in txt:
        plan.append({
            "action":
                "add_filter",
            "target":
                "freeze_authority_check"
        })

    return plan






def extract_strategy_rr(strategy_file):

    import re
    from pathlib import Path

    config = Path(
        "projects/config.py"
    )

    if not config.exists():
        return {}

    src = config.read_text(
        errors="ignore"
    )

    tp = re.search(
        r'TAKE_PROFIT_MULTIPLIER.*?"([0-9.]+)"',
        src
    )

    sl = re.search(
        r'STOP_LOSS_PERCENT.*?"([0-9.]+)"',
        src
    )

    return {
        "tp_expr":
            tp.group(1) if tp else None,

        "sl_expr":
            sl.group(1) if sl else None
    }


def analyze_strategy(strategy_file):

    return StrategyASTAnalyzer(
        strategy_file
    ).analyze()



def enqueue_optimization_tasks(tasks):

    from pathlib import Path
    import json

    queue_file = Path(
        "memory/task_queue.json"
    )

    if queue_file.exists():

        queue = json.loads(
            queue_file.read_text()
        )

    else:
        queue = []

    for task in tasks:

        if task not in queue:
            queue.append(task)

    queue_file.write_text(
        json.dumps(
            queue,
            indent=2
        )
    )





def detect_unreachable_branches(score_rules):

    unreachable = []

    seen = {}

    for rule in score_rules:

        cond = str(
            rule["condition"]
        )

        if cond in seen:

            unreachable.append({
                "condition": cond,
                "reason": "duplicate branch"
            })

        seen[cond] = True

    return unreachable


def detect_impossible_conditions(
    buy_conditions
):

    import re

    impossible = []

    for cond in buy_conditions:

        txt = cond.lower()

        if (
            "> 1000000000000" in txt
            or "< -1" in txt
        ):
            impossible.append(cond)

        m = re.search(
            r'age\s*<\s*(-?\d+)',
            txt
        )

        if m:

            if int(m.group(1)) < 0:

                impossible.append(cond)

    return impossible


def detect_conflicting_filters(
    buy_conditions
):

    conflicts = []

    txt = " ".join(
        buy_conditions
    )

    if (
        "age < 10" in txt
        and "age > 60" in txt
    ):
        conflicts.append(
            "age filter conflict"
        )

    return conflicts



def estimate_rr_ratio(result):

    src = result.get(
        "rr_source",
        {}
    )

    try:

        tp_mult = float(
            src.get(
                "tp_expr",
                0
            )
        )

        sl_pct = float(
            src.get(
                "sl_expr",
                0
            )
        )

        if tp_mult <= 0 or sl_pct <= 0:
            return None

        reward = tp_mult - 1
        risk = sl_pct / 100

        if risk <= 0:
            return None

        return round(
            reward / risk,
            2
        )

    except Exception:
        return None


def estimate_expected_winrate(
    result
):

    score = 50

    if result.get(
        "overlapping_rules"
    ):
        score -= 5

    if result.get(
        "dead_conditions"
    ):
        score -= 5

    if (
        "missing holder distribution check"
        in result.get(
            "recommendations",
            []
        )
    ):
        score -= 10

    return max(
        0,
        min(score, 100)
    )


def strategy_quality_score(
    result
):

    score = 100

    score -= (
        len(
            result.get(
                "dead_conditions",
                []
            )
        ) * 5
    )

    score -= (
        len(
            result.get(
                "overlapping_rules",
                []
            )
        ) * 5
    )

    score -= (
        len(
            result.get(
                "recommendations",
                []
            )
        ) * 10
    )

    return max(
        score,
        0
    )


def generate_patch_suggestions(
    result
):

    patches = []

    for dead in result.get(
        "dead_conditions",
        []
    ):

        patches.append({
            "type": "remove_condition",
            "target": dead["condition"]
        })

    for overlap in result.get(
        "overlapping_rules",
        []
    ):

        patches.append({
            "type": "merge_overlap",
            "field": overlap["field"]
        })

    return patches


if __name__ == "__main__":

    from pprint import pprint

    pprint(
        analyze_strategy(
            "projects/strategy.py"
        )
    )




