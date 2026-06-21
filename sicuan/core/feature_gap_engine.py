FEATURE_PRIORITY = {
    "trailing_stop": {
        "depends": [
            "position_restore",
            "stop_loss",
            "take_profit"
        ],
        "targets": [
            "risk_manager.py",
            "strategy.py"
        ],
        "instruction": (
            "Implement trailing stop loss production logic. "
            "Integrate with existing position monitoring, "
            "preserve stop_loss and take_profit behavior."
        )
    }
}


def get_missing_repairs(trace_ctx):
    repairs = []
    missing = trace_ctx.get("features_missing", [])

    for feat in missing:
        if feat in FEATURE_PRIORITY:
            data = FEATURE_PRIORITY[feat]
            repairs.append({
                "feature": feat,
                "targets": data["targets"],
                "instruction": data["instruction"]
            })

    return repairs
