"""``python -m orgindex_schema`` prints the canonical JSON Schema to stdout.

python -m orgindex_schema > index.schema.json
"""

from .schema import dumps_canonical, generate_json_schema


def main() -> None:
    print(dumps_canonical(generate_json_schema()))


if __name__ == "__main__":
    main()
