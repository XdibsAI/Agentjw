import json
from pathlib import Path

from sicuan.core.intelligence.capability_graph import CapabilityGraph
from sicuan.core.intelligence.endpoint_registry import EndpointRegistry
from sicuan.core.intelligence.runtime_intelligence import RuntimeIntelligence
from sicuan.core.intelligence.project_operator import ProjectOperator



ROOT="/home/dibs/agentjw"


def run():

    print("================================")
    print(" SiCuan Integration Brain V3")
    print(" Capability Intelligence Layer")
    print("================================")


    graph_engine=CapabilityGraph(ROOT)

    graph=graph_engine.scan()


    endpoints=EndpointRegistry(ROOT).scan()


    runtime=RuntimeIntelligence().analyze(graph)


    operator=ProjectOperator().build_context(
        runtime
    )


    report={

        "system":runtime,

        "graph":graph,

        "endpoints":endpoints,

        "operator_context":operator

    }


    out=Path(
        ROOT+"/sicuan_audit_report/integration_v3.json"
    )


    out.write_text(
        json.dumps(
            report,
            indent=2
        )
    )


    print("Saved:",out)



if __name__=="__main__":
    run()
