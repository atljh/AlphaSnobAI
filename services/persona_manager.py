import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from config.settings import Settings
from services.memory import Message

logger = logging.getLogger(__name__)


@dataclass
class Persona:
    name: str
    display_name: str
    description: str
    system_prompt: str
    response_guidelines: Dict[str, Any]
    tone_mapping: Dict[str, Any]
    language_instructions: str
    short_templates: Optional[Dict[str, List[str]]] = None

    def __repr__(self):
        return f"Persona({self.name})"


class PersonaManager:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.personas: Dict[str, Persona] = {}
        self.prompts_dir = settings.base_dir / "prompts"

        self._load_all_personas()
        logger.info(f"PersonaManager initialized with {len(self.personas)} personas")

    def _load_all_personas(self):
        persona_files = {
            'alphasnob': 'alphasnob_troll.yaml',
            'normal': 'normal_user.yaml',
            'owner': 'owner_style.yaml'
        }

        for persona_name, filename in persona_files.items():
            filepath = self.prompts_dir / filename
            if filepath.exists():
                try:
                    persona = self._load_persona_from_yaml(filepath)
                    self.personas[persona_name] = persona
                    logger.info(f"Loaded persona: {persona_name}")
                except Exception as e:
                    logger.error(f"Failed to load persona {persona_name}: {e}")
            else:
                logger.warning(f"Persona file not found: {filepath}")

    def _load_persona_from_yaml(self, filepath: Path) -> Persona:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        persona_data = data.get('persona', {})

        return Persona(
            name=persona_data.get('name', 'unknown'),
            display_name=persona_data.get('display_name', 'Unknown'),
            description=persona_data.get('description', ''),
            system_prompt=data.get('system_prompt', ''),
            response_guidelines=data.get('response_guidelines', {}),
            tone_mapping=data.get('tone_mapping', {}),
            language_instructions=data.get('language_instructions', ''),
            short_templates=data.get('short_templates')
        )

    def get_persona_for_context(
        self,
        user_id: int,
        chat_id: int,
        user_profile: Optional[Any] = None
    ) -> Persona:

        if user_id in self.settings.persona.user_overrides:
            persona_name = self.settings.persona.user_overrides[user_id]
            logger.debug(f"Using user override persona: {persona_name} for user {user_id}")
        elif chat_id in self.settings.persona.chat_overrides:
            persona_name = self.settings.persona.chat_overrides[chat_id]
            logger.debug(f"Using chat override persona: {persona_name} for chat {chat_id}")
        elif user_profile and hasattr(user_profile, 'preferred_persona') and user_profile.preferred_persona:
            persona_name = user_profile.preferred_persona
            logger.debug(f"Using profile preferred persona: {persona_name}")
        else:
            persona_name = self.settings.persona.default_mode
            logger.debug(f"Using default persona: {persona_name}")

        if persona_name not in self.personas:
            logger.warning(f"Persona {persona_name} not found, falling back to alphasnob")
            persona_name = 'alphasnob'

        return self.personas[persona_name]

    def generate_prompt(
        self,
        persona: Persona,
        incoming_message: str,
        context_messages: List[Message],
        sender_name: str,
        tone: str,
        detected_language: str,
        corpus_examples: Optional[List[str]] = None,
        owner_samples: Optional[List[str]] = None
    ) -> tuple[str, str]:

        system_prompt = persona.system_prompt

        system_prompt = system_prompt.replace('DETECTED_LANGUAGE', detected_language)

        if tone in persona.tone_mapping:
            tone_instruction = persona.tone_mapping[tone].get('instruction', '')
            if tone_instruction:
                system_prompt += f"\n\nTONE: {tone_instruction}"

        if corpus_examples and persona.name == 'alphasnob':
            examples_text = "\n".join(f"- {ex}" for ex in corpus_examples[:12])
            system_prompt += f"\n\nSTYLE EXAMPLES FROM CORPUS:\n{examples_text}"

        if owner_samples and persona.name == 'owner':
            samples_text = "\n".join(f"- {sample}" for sample in owner_samples[:20])
            system_prompt += f"\n\nOWNER_SAMPLES (study these carefully):\n{samples_text}"

        if persona.language_instructions:
            system_prompt += f"\n\n{persona.language_instructions}"

        context_str = self._build_context_string(context_messages)

        user_prompt = f"""CONVERSATION CONTEXT:
{context_str}

NEW MESSAGE from {sender_name}:
{incoming_message}

Respond in the style of {persona.display_name}."""

        return system_prompt, user_prompt

    def _build_context_string(self, context_messages: List[Message]) -> str:
        if not context_messages:
            return "No context."

        context_lines = []
        for msg in context_messages[-20:]:
            context_lines.append(f"{msg.username}: {msg.text}")

        return "\n".join(context_lines)

    def get_short_template(self, persona_name: str, tone: str) -> Optional[str]:
        if persona_name not in self.personas:
            return None

        persona = self.personas[persona_name]
        if not persona.short_templates:
            return None

        if tone not in persona.short_templates:
            tone = 'neutral'

        if tone in persona.short_templates:
            import random
            templates = persona.short_templates[tone]
            return random.choice(templates) if templates else None

        return None

    def get_persona_by_name(self, name: str) -> Optional[Persona]:
        return self.personas.get(name)

    def list_personas(self) -> List[str]:
        return list(self.personas.keys())
