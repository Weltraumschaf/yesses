from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class Template:
    def __init__(self, filename, template):
        self.filename = Path(filename)
        self.template = Path(template)
    
    def run(self, alertslist):
        file_loader = FileSystemLoader(str(self.template.parent))
        env = Environment(loader=file_loader)
        template = env.get_template(self.template.name)
        output = template.render(**alertslist.get_vars())
        
        self.filename.write_text(output)
