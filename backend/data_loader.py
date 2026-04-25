import json
from pathlib import Path


def load_smk_data():
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    data_path = project_root / "data" / "smk_data.json"

    with open(data_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data