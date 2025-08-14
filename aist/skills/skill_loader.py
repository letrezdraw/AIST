# aist/skills/skill_loader.py
import os
import importlib
import json
import logging
from pathlib import Path
from aist.core.ipc.protocol import INIT_STATUS_UPDATE # New import

log = logging.getLogger(__name__)

class SkillManager:
    def __init__(self, event_broadcaster, skills_dir="aist/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills = {}
        self.intents = {}
        self.event_broadcaster = event_broadcaster # Store the broadcaster
        self._load_skills()

    def _register_intent(self, skill_id, intent_name, intent_data):
        """Internal method to register an intent from a skill."""
        handler = intent_data.get("handler")
        if not callable(handler):
            log.error(f"Intent handler for '{intent_name}' in skill '{skill_id}' is not callable.")
            return
        
        # Store the full intent data, linking it back to the skill
        self.intents[intent_name] = {
            "skill_id": skill_id,
            "phrases": intent_data.get("phrases", []),
            "handler": handler,
            "parameters": intent_data.get("parameters", [])
        }
        log.info(f"Registered intent '{intent_name}' for skill '{skill_id}'.")

    def _load_skills(self):
        """Discovers, loads, and registers all valid skills."""
        log.info(f"Searching for skills in '{self.skills_dir}'...")
        if not self.skills_dir.is_dir():
            log.warning(f"Skills directory not found: {self.skills_dir}")
            self.event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "skills", "status": "failed", "error": f"Skills directory not found: {self.skills_dir}"}) # Send error update
            return

        loaded_count = 0
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "__init__.py").exists():
                skill_id = skill_dir.name
                manifest_path = skill_dir / "skill.json"

                if not manifest_path.exists():
                    log.warning(f"Skipping skill '{skill_id}': missing skill.json.")
                    continue

                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)

                    module_path = f"aist.skills.{skill_id}"
                    skill_module = importlib.import_module(module_path)
                    
                    if not hasattr(skill_module, 'create_skill'):
                        log.warning(f"Skipping skill '{skill_id}': missing create_skill() function.")
                        continue

                    skill_instance = skill_module.create_skill()
                    skill_instance._register(skill_id)
                    skill_instance.register_intents(
                        lambda intent_name, intent_data: self._register_intent(skill_id, intent_name, intent_data)
                    )
                    
                    self.skills[skill_id] = {"instance": skill_instance, "manifest": manifest}
                    log.info(f"Successfully loaded skill '{manifest.get('name', skill_id)}' (v{manifest.get('version', 'N/A')}).")
                    loaded_count += 1

                except Exception as e:
                    log.error(f"Failed to load skill '{skill_id}': {e}", exc_info=True)
        
        if loaded_count > 0:
            self.event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "skills", "status": "initialized", "count": loaded_count}) # Send update
        else:
            self.event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "skills", "status": "failed", "error": "No skills loaded."})

# Global instance for easy access across the application
skill_manager = None

def initialize_skill_manager(event_broadcaster):
    """Initializes the global skill_manager instance."""
    global skill_manager
    if skill_manager is None:
        skill_manager = SkillManager(event_broadcaster)
    return skill_manager
