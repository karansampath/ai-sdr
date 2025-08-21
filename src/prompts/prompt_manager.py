from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class PromptManager:
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render_template(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

    def get_system_prompt(self, service_type: str, **kwargs) -> str:
        template_map = {
            "lead_qualification": "lead_qualification_system.j2",
            "message_personalization": "message_personalization_system.j2"
        }
        if service_type not in template_map:
            raise ValueError(f"Unknown service type: {service_type}")
        return self.render_template(template_map[service_type], **kwargs)

    def get_user_prompt(self, service_type: str, **kwargs) -> str:
        template_map = {
            "lead_qualification": "lead_qualification_user.j2",
            "message_personalization": "message_personalization_user.j2"
        }
        if service_type not in template_map:
            raise ValueError(f"Unknown service type: {service_type}")
        return self.render_template(template_map[service_type], **kwargs)

# Global prompt manager instance
prompt_manager = PromptManager()
