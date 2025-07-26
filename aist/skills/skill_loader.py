# skills/skill_loader.py
import os
import importlib
import inspect
import logging

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

    for filename in os.listdir(skills_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"skills.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if hasattr(func, '_is_aist_skill'):
                        skill_name = func.__name__
                        available_skills[skill_name] = func
                        
                        docstring = inspect.getdoc(func)
                        if docstring:
                            sig = inspect.signature(func)
                            params = ", ".join(sig.parameters.keys())
                            first_line = docstring.split('\n')[0]
                            skills_prompt_fragment += f"- {skill_name}({params}): {first_line}\n"
                        log.info(f"Discovered skill: '{skill_name}' in {module_name}")
            except Exception as e:
                log.error(f"Failed to load skills from {module_name}: {e}", exc_info=True)

    if not available_skills:
        log.warning("No skills were discovered. The assistant will only have 'chat' and 'quit' capabilities.")
        
    return available_skills, skills_prompt_fragment