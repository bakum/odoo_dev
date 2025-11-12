import inspect
import docstring_parser
from pydantic import Field, create_model
from typing import Optional, Dict, Any, Callable, get_type_hints


def parse_docstring(func: Callable) -> Dict[str, Any]:
    """
    Extracts the main description, parameter descriptions, and return type description from a function's docstring.

    :param func: The function from which to parse the docstring.
    :type func: Callable

    :return: A dictionary containing the summary, parameter descriptions, and return description.
    :rtype: Dict[str, Any]
    """

    doc = docstring_parser.parse(func.__doc__ or "")
    summary = doc.short_description or "No description provided."
    if doc.long_description:
        summary += "\n\n" + doc.long_description
    param_descriptions = {p.arg_name: p.description for p in doc.params}
    return_description = doc.returns.description if doc.returns else "No return description."
    return {
        "summary": summary.strip() if summary else "",
        "params": param_descriptions,
        "return": return_description.strip() if return_description else "",
    }


def ai_tool(condition: Optional[Callable] = None) -> Callable:
    """
    Decorator to mark a function as an AI tool.

    :param condition: A function which receives the current AI thread as parameter.
                      The result of this function decides if the tool would be
                      included in the current thread or not.
    :type condition: Callable

    :return: The decorated function.
    :rtype: Callable
    """
    def decorator(func: Callable) -> Callable:
        setattr(func, "ai_tool", True)
        setattr(func, "ai_condition", condition)
        return func

    return decorator


def ai_spec(func: Callable) -> Dict:
    """
    Generate OpenAPI spec from a function with descriptions taken from the docstring.

    :param func: The function to process.
    :type func: Callable

    :return: OpenAPI spec for the function.
    :rtype: Dict
    """
    type_hints = get_type_hints(func)
    signature = inspect.signature(func)
    doc_info = parse_docstring(func)
    param_docs = doc_info["params"]
    parameters = list(signature.parameters.keys())

    fields = {}
    for index, param_name in enumerate(parameters):
        if index == 0 and (param_name == "self" or param_name == "cls"):
            continue
        param = signature.parameters[param_name]
        param_type = type_hints.get(param_name, str)
        param_desc = param_docs.get(param_name, "No description provided.")
        default = ... if param.default == inspect.Parameter.empty else param.default
        # Use Field to attach description
        fields[param_name] = (param_type, Field(default, description=param_desc))

    # Dynamically create a Pydantic model for the parameters
    ParamModel = create_model(f"{func.__name__}_params", **fields)
    param_schema = ParamModel.model_json_schema()
    param_schema.pop('title')

    ai_spec = {
        "name": func.__name__,
        "description": doc_info["summary"],
        "parameters": param_schema,
    }
    return ai_spec
