from typing import Any, Dict, List, Optional
from ninja import Schema

class GeneratedFile(Schema):
    path: str
    content: str
    type: str

class GeneratePrototypeResponse(Schema):
    message: str
    files: List[GeneratedFile]

class GeneratePrototypeRequest(Schema):
    prompt: str = ""
    model: str = "gemini-1.5-flash"
    layout_config: Optional[Dict[str, Any]] = None
    interface_data_override: Optional[Dict[str, Any]] = None
    inject_click_handlers: bool = False
