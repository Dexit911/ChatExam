# === Built-in ===
from dataclasses import dataclass
from typing import List

@dataclass
class SEBsettings:
    browser_view_mode: bool
    allow_quit: bool
    allow_clipboard: bool
    allow_spell_check: bool

    @property
    def view_mode_str(self) -> str:
        return "1" if self.browser_view_mode else "0"

    @property
    def allow_quit_str(self) -> str:
        return "true" if self.allow_quit else "false"

    @property
    def allow_clipboard_str(self) -> str:
        return "true" if self.allow_clipboard else "false"

    def to_xml_values(self) -> dict:
        """Helps to extract seb config data to xml string created in seb_manager"""
        return {
            "viewMode": self.view_mode_str,
            "allowQuit": self.allow_quit_str,
            "allowClipboard": self.allow_clipboard_str,
            "allowSpellCheck": self.allow_clipboard_str
        }

@dataclass
class ExamData:
    teacher_id: int
    title: str
    question_count: int
    ai_prompt: str
    allowed_extensions: List[str]
    file_count: int


