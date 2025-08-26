from .base_tool import BaseTool
from typing import List, Type
import os
import importlib

def get_tool_classes() -> List[Type[BaseTool]]:
    """
    Dynamically discovers and returns all tool classes.
    
    Returns:
        List[Type[BaseTool]]: List of tool classes.
    """

    tool_classes = []
    tools_dir = os.path.dirname(__file__)

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__") and filename != "base_tool.py" and filename != "register.py":
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f".{module_name}", package="src.tools")
                
                for name, obj in module.__dict__.items():
                    if isinstance(obj, type) and issubclass(obj, BaseTool) and obj is not BaseTool:
                        tool_classes.append(obj)

            except ImportError as e:
                print(f"Error importing tool module {module_name}: {e}")

    return tool_classes

def generate_tools_markdown(tool_classes: List[Type[BaseTool]]) -> str:
    """
    Generates a markdown string containing information about all tools.
    
    Args:
        tool_classes (List[Type[BaseTool]]): List of tool classes to generate markdown for.
    
    Returns:
        str: Markdown string containing information about all tools.
    """

    markdown_lines = []

    for tool_class in tool_classes:
        markdown_lines.append(f"- {tool_class.name}: {tool_class.description}")
        args_schema = tool_class.args_schema
        if args_schema and args_schema.model_fields:
            for field_name, field_info in args_schema.model_fields.items():
                if field_info.is_required():
                    req_or_default = "required"
                else:   
                    req_or_default = f"default = {field_info.default}"
                
                arg_type = field_info.annotation.__name__
                arg_desc = field_info.description or ""
                
                markdown_lines.append(f"    - Args: `{field_name}` ({arg_type}, {req_or_default}) - {arg_desc}")

    return "\n".join(markdown_lines)