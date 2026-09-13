import openai
from google import genai
from pathlib import Path

# ── Code-start keywords used for prose-stripping ──────────────────────────────
_SV_START_KEYWORDS = (
    'module ', 'interface ', 'class ', 'package ', 'program ',
    'covergroup ', 'property ', '`', '//',
)
_C_START_KEYWORDS  = ('#include', '#ifndef', '#define', 'typedef', 'void ', 'int ', 'static ')
_PY_START_KEYWORDS = ('import ', 'from ', 'def ', 'class ', '#')


def _strip_prose(result: str, task_category: str) -> str:
    """
    Remove any leading prose lines the LLM wrote before the actual code.
    LLMs sometimes prefix output with 'Here is the completed file:' etc.
    """
    result = result.strip()

    # 1. Remove markdown fences if present
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        result = result.strip()

    # 2. Determine which start-keywords to look for
    if task_category in ("reference_model_c",):
        start_kws = _C_START_KEYWORDS
    elif task_category in ("reference_model_py",):
        start_kws = _PY_START_KEYWORDS
    else:
        start_kws = _SV_START_KEYWORDS

    # 3. Drop every leading line that doesn't start with a code keyword
    lines = result.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(stripped.startswith(kw) for kw in start_kws):
            return "\n".join(lines[i:])

    # If no keyword found, return as-is (safer than returning empty string)
    return result


def test_api_key(api_key: str, model_name: str = "") -> tuple[bool, str]:
    """
    Tests an LLM API key against the selected model.
    """
    api_key = api_key.strip()
    if not api_key:
        return False, "API key is empty."
        
    model_name = model_name.strip()
    if not model_name:
        return False, "Please select a model!"
        
    model_lower = model_name.lower()
    wants_openai  = "openai" in model_lower or "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower
    wants_gemini  = "gemini" in model_lower
    wants_claude  = "claude" in model_lower
    wants_deepseek = "deepseek" in model_lower
    
    is_claude_key    = api_key.startswith("sk-ant-")
    is_openai_key    = api_key.startswith("sk-") and not api_key.startswith("sk-or-") and not is_claude_key
    is_openrouter_key = api_key.startswith("sk-or-")
    is_gemini_key    = api_key.startswith("AIza") or api_key.startswith("AQ.")
    
    # OpenRouter supports almost all models — skip strict mismatch checks for it
    if not is_openrouter_key:
        if wants_openai and not (is_openai_key or is_openrouter_key):
            return False, f"Mismatch: You selected an OpenAI model ({model_name}) but provided a different API Key."
        if wants_gemini and not is_gemini_key:
            return False, f"Mismatch: You selected a Gemini model ({model_name}) but provided a different API Key."
        if wants_claude and not is_claude_key:
            return False, f"Mismatch: You selected a Claude model ({model_name}) but provided a non-Anthropic API Key."

    # ── Claude key test ───────────────────────────────────────────────────────
    if is_claude_key:
        try:
            import anthropic as anthropic_sdk
            client = anthropic_sdk.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model_name if model_name else "claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "Respond with exactly the word 'Hello'."}],
            )
            reply = response.content[0].text.strip() if response.content else ""
            if "hello" in reply.lower():
                return True, "Anthropic (Claude) Connected successfully"
            return True, f"Connected, but unexpected response: {reply}"
        except Exception as e:
            return False, f"Anthropic Error: {str(e)}"

    # ── OpenAI / OpenRouter key test ──────────────────────────────────────────
    if api_key.startswith("sk-"):
        try:
            if is_openrouter_key:
                client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            else:
                client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name if model_name else "gpt-3.5-turbo",
                messages=[{"role": "user", "content": "You are an AI assistant. Please respond with exactly the word 'Hello' to confirm connection."}],
                max_tokens=10
            )
            raw_content = response.choices[0].message.content
            reply = raw_content.strip() if raw_content else ""
            if "hello" in reply.lower():
                return True, "OpenAI Connected successfully"
            return True, f"Connected, but unexpected response: {reply}"
        except Exception as e:
            return False, f"OpenAI Error: {str(e)}"

    # ── Gemini key test ───────────────────────────────────────────────────────
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name if model_name else 'gemini-2.5-flash',
            contents="You are an AI assistant. Please respond with exactly the word 'Hello' to confirm connection."
        )
        reply = response.text.strip()
        if "hello" in reply.lower():
            return True, "Gemini Connected successfully"
        return True, f"Connected, but unexpected response: {reply}"
    except Exception as e:
        return False, f"Gemini Error: {str(e)}"


# ── Generation helpers ────────────────────────────────────────────────────────

def _call_gemini(api_key: str, prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Call Gemini to generate code."""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text.strip()


def _call_openai(api_key: str, prompt: str, model: str = "gpt-4o") -> str:
    """Call OpenAI (or OpenRouter) to generate code."""
    if api_key.startswith("sk-or-"):
        client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    else:
        client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=16000,   # Fix 1: was 4096 — large files were truncated mid-code
    )
    raw_content = response.choices[0].message.content
    return raw_content.strip() if raw_content else ""


def _call_anthropic(api_key: str, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> str:
    """Call Anthropic Claude to generate code."""
    try:
        import anthropic as anthropic_sdk
    except ImportError:
        return "Error: 'anthropic' Python package is not installed. Please install it using `pip install anthropic` to use Claude models."
        
    client = anthropic_sdk.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip() if response.content else ""


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_ai_artifact(
    task_category: str,
    model_name: str,
    api_key: str,
    project_files: list[str],
    skeleton_path: str,
    user_prompt: str = "",
    ref_doc_file: str = None,
) -> str:
    """
    Generalized function to generate any UVM artifact using the RAG architecture.
    """
    if not model_name or not model_name.strip():
        raise ValueError("Model is missing! Please select a model.")
    
    import sys
    proj_root = str(Path(__file__).parent.parent)
    if proj_root not in sys.path:
        sys.path.insert(0, proj_root)

    from .prompt_builder import build_task_prompt

    prompt = build_task_prompt(
        task_category=task_category,
        target_skeleton_file=skeleton_path,
        project_context_files=project_files,
        user_instructions=user_prompt,
        ref_doc_file=ref_doc_file,
    )

    # Fix 5: Route Claude keys correctly instead of falling into OpenAI branch
    key = api_key.strip()
    if key.startswith("sk-ant-"):
        result = _call_anthropic(key, prompt, model=model_name or "claude-3-5-sonnet-20241022")
    elif key.startswith("sk-"):
        result = _call_openai(key, prompt, model=model_name or "gpt-4o")
    else:
        result = _call_gemini(key, prompt, model=model_name or "gemini-2.5-flash")

    # Fix 2: Strip markdown fences AND any leading prose the LLM added before the code
    result = _strip_prose(result, task_category)

    return result


def generate_assertions(
    model_name: str,
    api_key: str,
    rtl_path: str,
    skeleton_path: str,
    user_prompt: str = "",
    rag_k: int = 6,  # Left for backward compatibility, unused
) -> str:
    """
    Backward compatibility wrapper for the Frontend to generate assertions.
    """
    return generate_ai_artifact(
        task_category="assertions",
        model_name=model_name,
        api_key=api_key,
        project_files=[rtl_path],
        skeleton_path=skeleton_path,
        user_prompt=user_prompt
    )
