#!/usr/bin/env python3
import os
import sys
import json
import re

def load_input(input_file="input.json"):
    """
    Load onboarding parameters from JSON file, searching cwd or script directory.
    """
    # Try current directory
    if os.path.isfile(input_file):
        path = input_file
    else:
        # Try script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alt = os.path.join(script_dir, input_file)
        if os.path.isfile(alt):
            path = alt
        else:
            sys.stderr.write(f"ERROR: input file '{input_file}' not found in cwd or script directory.\n")
            sys.exit(1)

    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"ERROR: failed to parse JSON '{path}': {e}\n")
            sys.exit(1)


def build_context(data):
    """
    Build a flat context dict from input JSON and derive repo names.
    """
    ctx = {}
    # Copy scalar values from JSON, uppercased
    for k, v in data.items():
        if isinstance(v, (str, int, float, bool)):
            ctx[k.upper()] = v
    # Derived repo names
    base = f"{data['organization_code']}-{data['lob_code']}-{data['app_code']}-{data['application_name']}"
    ctx['FOUNDATION_REPO'] = f"{base}-foundation-repo"
    ctx['INFRA_REPO']      = f"{base}-infra-repo"
    ctx['APP_REPO']        = f"{base}-app-repo"
    ctx['REPO_VISIBILITY'] = f"private"
    ctx['GITHUB_ORGANIZATION'] = f"pathakas"
    return ctx


def render_template(template_path, output_path, context):
    """
    Renders a .tpl file by replacing ${KEY} with context or environment variables.
    """
    if not os.path.isfile(template_path):
        sys.stderr.write(f"ERROR: template '{template_path}' not found.\n")
        sys.exit(1)

    content = open(template_path).read()

    # Replacement function
    def repl(m):
        key = m.group(1)
        if key in context:
            return str(context[key])
        return os.environ.get(key, m.group(0))

    rendered = re.sub(r"\$\{(\w+)\}", repl, content)

    try:
        with open(output_path, 'w') as f:
            f.write(rendered)
    except Exception as e:
        sys.stderr.write(f"ERROR: cannot write '{output_path}': {e}\n")
        sys.exit(1)

    print(f"Rendered '{output_path}' from '{template_path}'")


def main():
    # Usage: render_tfvars.py [input.json]
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'input.json'
    data = load_input(input_file)
    context = build_context(data)
    # Merge in environment variables (so placeholders can come from GH secrets, etc.)
    for k, v in os.environ.items():
        context[k] = v

    tpl = 'terraform.tfvars.tpl'
    out = 'terraform.tfvars'
    render_template(tpl, out, context)


if __name__ == '__main__':
    main()
