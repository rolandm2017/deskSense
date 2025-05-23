# scripts/sync_types.py
import os
import sys
from pathlib import Path


def sync_types():
    # Change to project root
    current = Path(__file__).resolve()

    # Walk up until we find the project root (look for both activitytracker and chrome folders)
    project_root = None
    for parent in current.parents:
        if (parent / "activitytracker").exists() and (parent / "chrome").exists():
            project_root = parent
            break

    if not project_root:
        raise Exception(
            "Could not find project root with both 'activitytracker' and 'chrome' folders"
        )

    print(f"Found project root: {project_root}")
    os.chdir(project_root)

    output_path = Path("chrome/src/interface/payloads.ts")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Add src to Python path so we can import our models
    sys.path.insert(0, str(project_root / "src"))

    try:
        from activitytracker.object.pydantic_video_dto import (
            NetflixPlayerChange,
            NetflixTabChange,
            YouTubePlayerChange,
            YouTubeTabChange,
        )

        # Generate JSON schemas
        models = {
            "YouTubeTabChange": YouTubeTabChange,
            "YouTubePlayerChange": YouTubePlayerChange,
            "NetflixTabChange": NetflixTabChange,
            "NetflixPlayerChange": NetflixPlayerChange,
        }

        ts_content = "// Auto-generated from Pydantic models\n\n"

        for name, model in models.items():
            schema = model.model_json_schema()
            ts_content += convert_schema_to_ts(name, schema)

        # Write to file
        with open(output_path, "w") as f:
            f.write(ts_content)

        print("✅ TypeScript interfaces updated!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to install: pip install pydantic-to-typescript")
    except Exception as e:
        print(f"❌ Error: {e}")


def convert_schema_to_ts(name: str, schema: dict) -> str:
    """Convert JSON schema to TypeScript interface"""
    props = schema.get("properties", {})

    ts = f"export interface {name} {{\n"
    for prop_name, prop_info in props.items():
        prop_type = get_ts_type(prop_info)
        required = prop_name in schema.get("required", [])
        optional = "" if required else "?"
        ts += f"  {prop_name}{optional}: {prop_type};\n"
    ts += "}\n\n"

    return ts


def get_ts_type(prop_info: dict) -> str:
    """Convert JSON schema type to TypeScript type"""
    prop_type = prop_info.get("type", "any")

    if prop_type == "string":
        return "string"
    elif prop_type == "integer" or prop_type == "number":
        return "number"
    elif prop_type == "boolean":
        return "boolean"
    elif prop_info.get("format") == "date-time":
        return "string"  # ISO date string
    else:
        return "any"


if __name__ == "__main__":
    sync_types()
