import os
import importlib
import inspect
import logging
import sys

log = logging.getLogger(__name__)

def aist_skill(func):
    """A decorator to mark functions as AIST skills."""
    func._is_aist_skill = True
    return func

def discover_skills() -> tuple[dict, str]:
    """
    Dynamically discovers and loads all functions marked with the @aist_skill decorator.

    Returns:
        A tuple containing:
            - A dictionary mapping skill names to their function objects.
            - A formatted string describing the skills for the LLM prompt.
    """
    available_skills = {}
    skills_prompt_fragment = ""
    skills_dir = os.path.dirname(__file__)

    # Add the parent directory of this file to sys.path to fix import issues
    parent_dir = os.path.abspath(os.path.join(skills_dir, os.pardir))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    for filename in os.listdir(skills_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"aist.skills.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if hasattr(func, '_is_aist_skill'):
                        skill_name = func.__name__
                        available_skills[skill_name] = func
                        
                        docstring = inspect.getdoc(func)
                        if docstring:
                            sig = inspect.signature(func)
                            # Create a more descriptive parameter string for the LLM, including type hints.
                            params = ", ".join(f"{p.name}: {p.annotation.__name__}" for p in sig.parameters.values())
                            first_line = docstring.strip().split('\n')[0]
                            skills_prompt_fragment += f"- {skill_name}({params}): {first_line}\n"
                        log.info(f"Discovered skill: '{skill_name}' in {module_name}")
            except Exception as e:
                log.error(f"Failed to load skills from {module_name}: {e}", exc_info=True)

    if not available_skills:
        log.warning("No skills were discovered. The assistant will only have 'chat' and 'quit' capabilities.")
        
    return available_skills, skills_prompt_fragment
