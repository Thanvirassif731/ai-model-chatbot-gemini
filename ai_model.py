from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("Install python-dotenv")
    print("pip install python-dotenv")
    sys.exit(1)

try:
    from google import genai
except ImportError:
    print("Install google-genai")
    print("pip install google-genai")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.syntax import Syntax
except ImportError:
    print("Install rich")
    print("pip install rich")
    sys.exit(1)

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory
except ImportError:
    print("Install prompt_toolkit")
    print("pip install prompt_toolkit")
    sys.exit(1)


# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("GEMINI_API_KEY missing in .env")
    sys.exit(1)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


# =========================================================
# RICH CONSOLE
# =========================================================

console = Console()


# =========================================================
# CHAT STORAGE
# =========================================================

CHAT_DIR = Path("chat_sessions")
CHAT_DIR.mkdir(exist_ok=True)

CURRENT_SESSION = (
    CHAT_DIR /
    f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
)

history = []


# =========================================================
# SYSTEM PROMPTS
# =========================================================

MODES = {
    "default": """
You are a helpful AI assistant.
Give clear and concise responses.
""",

    "coder": """
You are an expert software engineer.
Provide optimized code with explanations.
""",

    "teacher": """
You are an expert teacher.
Explain concepts step by step.
""",

    "research": """
You are a research assistant.
Provide detailed technical explanations.
"""
}

current_mode = "default"


# =========================================================
# GEMINI CLIENT
# =========================================================

# Client and chat are created in `main()` via `build_client()`.


# =========================================================
# SAVE HISTORY
# =========================================================

def save_chat():
    with open(CURRENT_SESSION, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# =========================================================
# LOAD SESSION
# =========================================================

def load_session(path):
    global history

    with open(path, "r", encoding="utf-8") as f:
        history = json.load(f)

    console.print(
        f"[green]Loaded session:[/green] {path}"
    )


# =========================================================
# CLEAR SCREEN
# =========================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# =========================================================
# HELP MENU
# =========================================================

def show_help():
    help_text = """
[bold cyan]Available Commands[/bold cyan]

/help               Show commands
/clear              Clear terminal
/history            Show chat history
/save               Save current session
/sessions           Show saved sessions
/load               Load session
/mode               Change assistant mode
/tokens             Show token estimate
/exit               Exit chatbot

[bold yellow]Modes[/bold yellow]

default
coder
teacher
research
"""

    console.print(Panel(help_text))


# =========================================================
# SHOW HISTORY
# =========================================================

def show_history():
    if not history:
        console.print("[yellow]No history available.[/yellow]")
        return

    for item in history:
        role = item["role"]
        content = item["content"]

        color = "cyan" if role == "user" else "green"

        console.print(
            f"[bold {color}]{role.upper()}:[/bold {color}]"
        )

        console.print(Markdown(content))
        console.print()


# =========================================================
# TOKEN ESTIMATE
# =========================================================

def estimate_tokens():
    total_chars = sum(
        len(item["content"])
        for item in history
    )

    estimated_tokens = total_chars // 4

    console.print(
        Panel(
            f"Estimated Tokens: {estimated_tokens}",
            title="Token Usage"
        )
    )



def list_sessions():
    files = list(CHAT_DIR.glob("*.json"))

    if not files:
        console.print("[yellow]No sessions found.[/yellow]")
        return

    console.print(
        Panel(
            "\n".join(str(f) for f in files),
            title="Saved Sessions"
        )
    )


# =========================================================
# CHANGE MODE
# =========================================================

def change_mode():
    global current_mode

    console.print("\nAvailable modes:")

    for mode in MODES:
        console.print(f"- {mode}")

    selected = input("\nEnter mode: ").strip()

    if selected in MODES:
        current_mode = selected

        console.print(
            f"[green]Mode changed to:[/green] {selected}"
        )
    else:
        console.print("[red]Invalid mode[/red]")


# =========================================================
# STREAM RESPONSE
# =========================================================

def stream_response(user_text):
    global history

    full_prompt = MODES[current_mode] + "\n\n"

    for item in history[-10:]:
        full_prompt += (
            f"{item['role']}: "
            f"{item['content']}\n"
        )

    full_prompt += f"user: {user_text}"

    retries = 3

    for attempt in range(retries):
        try:
            start_time = time.time()

            response_stream = chat.send_message_stream(
                full_prompt
            )

            console.print(
                "\n[bold green]Gemini:[/bold green] ",
                end=""
            )

            final_text = ""

            for chunk in response_stream:

                chunk_text = getattr(
                    chunk,
                    "text",
                    ""
                )

                final_text += chunk_text

                print(
                    chunk_text,
                    end="",
                    flush=True
                )

            elapsed = round(
                time.time() - start_time,
                2
            )

            print()

            console.print(
                f"\n[dim]Response time: {elapsed}s[/dim]"
            )

            history.append({
                "role": "user",
                "content": user_text,
                "time": str(datetime.now())
            })

            history.append({
                "role": "assistant",
                "content": final_text,
                "time": str(datetime.now())
            })

            save_chat()

            return

        except Exception as exc:

            console.print(
                f"\n[red]Error:[/red] {exc}"
            )

            if attempt < retries - 1:
                console.print(
                    "[yellow]Retrying in 5 seconds...[/yellow]"
                )

                time.sleep(5)

            else:
                console.print(
                    "[bold red]Failed after retries.[/bold red]"
                )


# =========================================================
# MAIN
# =========================================================

# (Old interactive main removed — replaced by the consolidated main below.)
# Define conversation styles with their system prompts
CONVERSATION_STYLES = {
    "1": {
        "name": "Funny",
        "description": "Humorous and witty with jokes and puns",
        "prompt": (
            "You are a hilarious AI assistant who loves using humor, puns, and witty jokes. "
            "Keep responses entertaining and fun while still being helpful. Use emojis when appropriate!"
        ),
    },
    "2": {
        "name": "Strict",
        "description": "Professional, formal, and concise",
        "prompt": (
            "You are a professional and formal AI assistant. Provide concise, structured responses. "
            "Use clear language without unnecessary elaboration. Maintain a professional tone throughout."
        ),
    },
    "3": {
        "name": "Lengthy",
        "description": "Comprehensive and detailed explanations",
        "prompt": (
            "You are a thorough and comprehensive AI assistant. Provide detailed, in-depth explanations. "
            "Cover all aspects of the topic, provide examples, and elaborate thoroughly on your answers."
        ),
    },
    "4": {
        "name": "Casual",
        "description": "Friendly and conversational",
        "prompt": (
            "You are a friendly and casual AI companion. Use a warm, conversational tone. "
            "Feel free to be relaxed, use casual language, and build a friendly rapport with the user."
        ),
    },
    "5": {
        "name": "Technical",
        "description": "Expert-level technical depth and details",
        "prompt": (
            "You are an expert technical AI assistant. Provide deep technical insights and details. "
            "Use technical terminology appropriately, explain complex concepts, and go into implementation details."
        ),
    },
}


def build_client():
    try:
        from google import genai
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: google-genai. Install it with: pip install -r requirements.txt"
        ) from exc

    return genai.Client(api_key=API_KEY)



def select_conversation_style() -> tuple[str, str]:
    """Display style options and get user selection. Returns (style_name, system_prompt)"""
    print("\n" + "=" * 60)
    print("🎭 Choose Your Conversation Style")
    print("=" * 60)

    for key, style in CONVERSATION_STYLES.items():
        print(f"{key}. {style['name']:12} - {style['description']}")

    print("=" * 60)

    while True:
        choice = input("Select a style (1-5): ").strip()
        if choice in CONVERSATION_STYLES:
            selected_style = CONVERSATION_STYLES[choice]
            print(f"\n✅ Selected: {selected_style['name']} style\n")
            return selected_style["name"], selected_style["prompt"]
        else:
            print("❌ Invalid choice. Please select 1-5.")


def main() -> int:
    client = build_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Get user's preferred conversation style
    style_name, system_prompt = select_conversation_style()

    # create global chat so stream_response() can access it
    global chat
    chat = client.chats.create(model=model_name)

    # Initialize conversation with the system prompt
    try:
        initial_response = chat.send_message(
            f"[System Instructions: {system_prompt}]\n\n"
            "Ready to chat! Keep these instructions in mind for all future responses."
        )
    except Exception as exc:
        print(f"Error initializing chat: {exc}", file=sys.stderr)
        return 1

    print(f"Gemini chat ready using {model_name} ({style_name} style).")
    print('Type your message and press Enter. Type "exit" or "quit" to stop.')
    print("-" * 60)

    # Enter interactive loop
    while True:
        try:
            user_text = prompt("\nYou: ", history=InMemoryHistory(), multiline=False).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Exiting chatbot...[/bold red]")
            break

        if not user_text:
            continue

        if user_text == "/mode":
            change_mode()
            continue

        if user_text == "/tokens":
            estimate_tokens()
            continue

        if user_text in {"/exit", "exit", "quit"}:
            console.print("[bold red]Goodbye![/bold red]")
            break

        # CHAT RESPONSE
        stream_response(user_text)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()