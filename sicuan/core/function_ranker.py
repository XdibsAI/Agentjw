from collections import Counter

KEYWORDS = {
    "buy": [
        "_open_position",
        "execute_buy",
        "process_new_token",
        "_should_buy",
    ],
    "sell": [
        "_close_position",
        "execute_take_profit",
        "execute_stop_loss",
    ],
    "stop": [
        "check_stop_loss",
        "execute_stop_loss",
    ],
    "profit": [
        "check_take_profit",
        "execute_take_profit",
    ],
    "position": [
        "_open_position",
        "_close_position",
        "add_position",
        "remove_position",
    ],
    "wallet": [
        "get_balance",
        "load_paper_balance",
        "save_paper_balance",
    ],
}


def rank_functions(trace_ctx, instruction):

    text = instruction.lower()

    score = Counter()

    for keyword, funcs in KEYWORDS.items():
        if keyword in text:
            for fn in funcs:
                score[fn] += 10

    for fn in trace_ctx.get("top_functions", []):
        score[fn] += 1

    ranked = [x[0] for x in score.most_common(10)]

    return ranked
