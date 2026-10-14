"""``python -m orgindex_schema`` prints the canonical JSON Schema to stdout.

python -m orgindex_schema > index.schema.json
"""

import json

from .schema import generate_json_schema


def main() -> None:
    print(json.dumps(generate_json_schema(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
