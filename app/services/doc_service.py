import tempfile
from pathlib import Path

from docxtpl import DocxTemplate

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class DocService:
    def generate_docx(self, data: dict, template_name: str = "nmck_template.docx") -> Path:
        template_path = TEMPLATES_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        tpl = DocxTemplate(template_path)
        tpl.render(data)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        tpl.save(tmp.name)
        return Path(tmp.name)
