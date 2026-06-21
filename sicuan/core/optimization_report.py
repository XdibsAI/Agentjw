from pathlib import Path
import json
from datetime import datetime, timezone


class OptimizationReport:


    def __init__(
        self,
        folder="memory/optimization_reports"
    ):

        self.folder = Path(folder)

        self.folder.mkdir(
            parents=True,
            exist_ok=True
        )


    def write(
        self,
        data
    ):

        data["timestamp"] = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )


        path = (
            self.folder /
            "latest_report.json"
        )


        path.write_text(
            json.dumps(
                data,
                indent=2
            )
        )


        return str(path)
