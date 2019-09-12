#!/usr/bin/env python3

import inspect
import importlib
import subprocess
import logging
import yaml

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

logging.getLogger().setLevel(logging.INFO)

INFILE = Path('README.j2')
OUTFILE = Path('README.md')

modules = ['scan', 'discover']

template_modules = {}

for m in modules:
    module = importlib.import_module(f"yesses.{m}")
    classes = list(member[1] for member in inspect.getmembers(module) if type(member[1]) == type)
    template_modules[m] = classes

    for c in classes:
        print (f"Testing {m} {c.__name__}")
        c.selftest(standalone=False)


def jinja2_yaml_filter(obj):
    out = yaml.safe_dump(obj, default_flow_style=False, default_style='')
    if out.endswith("...\n"):
        return out[:-4]
    else:
        return out

res = subprocess.run(['./run.py', '--help'], stdout=subprocess.PIPE)
usage = str(res.stdout, 'ascii')

    
file_loader = FileSystemLoader(str(INFILE.parent))
env = Environment(loader=file_loader)
env.filters['yaml'] = jinja2_yaml_filter
template = env.get_template(INFILE.name)
output = template.render(modules=template_modules, usage=usage)
OUTFILE.write_text(output)
