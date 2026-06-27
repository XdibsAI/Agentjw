"""
trace_code - Trace dependency/symbol dengan Result Contract
"""

from sicuan.code_trace import trace_before_patch
from sicuan.core.result_contract import ResultContract
from core.logger import logger
import threading
import time


class TraceTimeout(Exception):
    pass


def execute(task: dict) -> dict:
    """Execute trace_code dengan Result Contract"""
    target = task.get("target", "")
    symbol = (target or "").strip()
    
    if not symbol:
        contract = ResultContract(
            success=False,
            action="trace_code",
            entity="",
            display="❌ Fungsi/symbol apa yang mau di-trace?",
            errors=["Fungsi/symbol apa yang mau di-trace?"]
        )
        return contract.to_dict()
    
    result_container = {"result": None, "error": None, "done": False}
    
    def trace_thread():
        try:
            result_container["result"] = trace_before_patch(symbol)
            result_container["done"] = True
        except Exception as e:
            result_container["error"] = str(e)
            result_container["done"] = True
    
    thread = threading.Thread(target=trace_thread)
    thread.daemon = True
    thread.start()
    
    timeout = 10
    start = time.time()
    while not result_container["done"] and (time.time() - start) < timeout:
        time.sleep(0.1)
    
    if not result_container["done"]:
        contract = ResultContract(
            success=False,
            action="trace_code",
            entity=symbol,
            display=f"❌ Trace timeout untuk '{symbol}' setelah 10 detik",
            errors=[f"Trace timeout untuk '{symbol}' setelah 10 detik"]
        )
        return contract.to_dict()
    
    if result_container["error"]:
        contract = ResultContract(
            success=False,
            action="trace_code",
            entity=symbol,
            display=f"❌ Trace error: {result_container['error']}",
            errors=[result_container['error']]
        )
        return contract.to_dict()
    
    result = result_container["result"]
    duration = time.time() - start
    
    # Konversi ke string
    if hasattr(result, "to_report"):
        trace_output = result.to_report()
    elif hasattr(result, "to_dict"):
        trace_output = str(result.to_dict())
    else:
        trace_output = str(result)
    
    logger.info(f"Trace {symbol}: {duration:.2f}s")
    
    contract = ResultContract(
        success=True,
        action="trace_code",
        entity=symbol,
        display=f"Trace {symbol}: selesai",
        metrics={"found": bool(trace_output)},
        confidence=0.95,
        duration=duration,
        data={"trace": trace_output}
    )
    return contract.to_dict()
