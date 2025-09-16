#!/usr/bin/env python3
"""
Environment setup utility - helps developers set up their .env file safely.
"""

import shutil
import sys
from pathlib import Path


def setup_environment(template: str = "minimal", force: bool = False) -> bool:
    """
    Set up local .env file from template.

    Args:
        template: Template to use ('minimal', 'development', 'example')
        force: Overwrite existing .env file
    """
    project_root = Path(__file__).parent
    env_file = project_root / ".env"

    # Template mapping
    templates = {
        "minimal": ".env.minimal",
        "development": ".env.development",
        "production": ".env.production",
        "example": ".env.example",
    }

    if template not in templates:
        return False

    template_file = project_root / templates[template]

    if not template_file.exists():
        return False

    # Check if .env already exists
    if env_file.exists() and not force:

        response = (
            input(
                "Do you want to:\n"
                "  [b]ackup and replace\n"
                "  [o]verwrite\n"
                "  [c]ancel\n"
                "Choice (b/o/c): "
            )
            .lower()
            .strip()
        )

        if response == "b":
            # Create backup
            backup_file = env_file.with_suffix(".env.backup")
            shutil.copy2(env_file, backup_file)
        elif response == "o":
            pass
        else:
            return False

    # Copy template to .env
    try:
        shutil.copy2(template_file, env_file)

        # Show what needs to be configured
        show_required_config()
        return True

    except Exception:
        return False


def show_required_config():
    """Show what configuration is required."""


def list_templates():
    """List available environment templates."""
    project_root = Path(__file__).parent
    templates = []

    for template_file in project_root.glob(".env.*"):
        if template_file.name not in [".env.backup"]:
            # Read description from file
            try:
                with open(template_file) as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                    description = next(
                        (
                            line[1:].strip()
                            for line in first_lines
                            if line.startswith("#") and len(line) > 10
                        ),
                        "Environment template",
                    )
            except:
                description = "Environment template"

            templates.append(
                {
                    "name": template_file.name,
                    "key": template_file.name.replace(".env.", ""),
                    "description": description,
                    "size": template_file.stat().st_size,
                }
            )

    for _template in templates:
        pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Environment setup utility")
    parser.add_argument(
        "--template",
        "-t",
        default="minimal",
        choices=["minimal", "development", "production", "example"],
        help="Template to use for .env file",
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing .env file without prompting"
    )
    parser.add_argument("--list", "-l", action="store_true", help="List available templates")

    args = parser.parse_args()

    if args.list:
        list_templates()
    else:
        success = setup_environment(args.template, args.force)
        sys.exit(0 if success else 1)
