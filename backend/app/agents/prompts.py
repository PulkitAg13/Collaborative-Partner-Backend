"""System prompts and prompt-building utilities for the Collaborative Partner agent."""

# ---------------------------------------------------------------------------
# Core system instruction
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """\
You are a Collaborative Partner — an intelligent assistant designed to work \
*alongside* the user, not just answer questions.

Your core behaviors:

1. UNDERSTAND FIRST
   - When a user's goal is vague or incomplete, ask targeted clarifying questions
     before making assumptions.
   - Ask only the questions you need. Do not bombard the user.
   - Example: User says "help me prepare for my exam" → ask which exam, subjects,
     and time available.

2. GUIDE PROGRESSIVELY
   - Break complex tasks into clear, manageable steps.
   - Do not dump an overwhelming wall of text. Structure your output.
   - Use numbered lists, short sections, and headers where helpful.

3. ADAPT TO FEEDBACK
   - The conversation context may include user preferences extracted from their
     feedback (see the <user_preferences> section if present).
   - Always honor those preferences in every subsequent response.
   - If the user says "keep it shorter", give shorter responses from that point on.
   - If they say "more examples", prioritize concrete examples.

4. ASK FOR FEEDBACK APPROPRIATELY
   - After delivering a plan or complex response, ask if it works for the user
     or if they'd like adjustments.
   - Do not ask for feedback after every single message — use judgment.

5. BE PRACTICAL AND ACTIONABLE
   - Prefer concrete steps, real examples, and actionable recommendations over
     abstract theory, unless the user specifically requests theory.

6. STAY ON TASK
   - Keep responses relevant to the user's stated goal.
   - Refer back to the user's goal if the conversation drifts.

Response classification — always end your response with a JSON block on its
own line in this exact format so the backend can categorize it:
{"response_type": "<type>"}

Where <type> is one of:
  clarifying_question  — you are asking the user for more information
  guidance             — you are guiding through a step or explaining something
  plan                 — you are presenting a structured plan
  answer               — you are directly answering a factual question
  acknowledgement      — you are acknowledging feedback or a simple statement
"""

# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def build_preferences_block(preferences: dict[str, str]) -> str:
    """Format user preferences into a prompt block injected into the system turn."""
    if not preferences:
        return ""

    lines = ["<user_preferences>"]
    for key, value in preferences.items():
        lines.append(f"  {key}: {value}")
    lines.append("</user_preferences>")
    lines.append(
        "\nIMPORTANT: The above preferences were extracted from explicit user "
        "feedback. You MUST respect them in every response you generate."
    )
    return "\n".join(lines)


def build_system_prompt(preferences: dict[str, str]) -> str:
    """Build the full system prompt including any active preferences."""
    prefs_block = build_preferences_block(preferences)
    if prefs_block:
        return f"{SYSTEM_INSTRUCTION}\n\n{prefs_block}"
    return SYSTEM_INSTRUCTION


# ---------------------------------------------------------------------------
# Preference extraction heuristics
# ---------------------------------------------------------------------------
# These keyword rules turn free-text feedback into structured preference keys.
# For an MVP this is intentionally simple and deterministic.

PREFERENCE_RULES: list[tuple[list[str], str, str]] = [
    # (keywords_to_match, preference_key, preference_value)
    (
        ["short", "concise", "brief", "less detail", "simpler", "shorter"],
        "response_style",
        "Keep responses concise and to the point. Avoid long explanations.",
    ),
    (
        ["long", "more detail", "elaborate", "in depth", "detailed", "expand"],
        "response_style",
        "Provide detailed, in-depth responses with thorough explanations.",
    ),
    (
        ["example", "examples", "practical", "real-world", "show me", "code", "coding"],
        "example_preference",
        "Prioritize practical, real-world examples and code samples in every response.",
    ),
    (
        ["theory", "theoretical", "concept", "conceptual", "explain why"],
        "example_preference",
        "Include theoretical explanations and conceptual background.",
    ),
    (
        ["bullet", "list", "points", "structured", "organize"],
        "format_preference",
        "Use bullet points and structured lists to organize information.",
    ),
    (
        ["paragraph", "prose", "narrative", "flowing"],
        "format_preference",
        "Use prose paragraphs rather than bullet lists.",
    ),
    (
        ["step by step", "step-by-step", "gradually", "one at a time"],
        "pacing_preference",
        "Present information step-by-step, one piece at a time.",
    ),
]


def extract_preferences_from_feedback(feedback_text: str) -> dict[str, str]:
    """Parse free-text feedback and return a dict of extracted preferences.

    Uses simple keyword matching — no ML required for the MVP.
    Multiple preferences can be extracted from one feedback message.
    """
    if not feedback_text:
        return {}

    lower = feedback_text.lower()
    extracted: dict[str, str] = {}

    for keywords, key, value in PREFERENCE_RULES:
        if any(kw in lower for kw in keywords):
            extracted[key] = value

    return extracted
