from __future__ import annotations

import os
import sys
from datetime import datetime

try:
	from dotenv import load_dotenv
except Exception:
	load_dotenv = None

try:
	from rich.console import Console
	from rich.panel import Panel
	from rich.text import Text
	from rich.align import Align
except ImportError as exc:
	raise SystemExit(
		"Missing dependency: rich. Install it with: pip install -r requirements.txt"
	) from exc


console = Console()


def build_client():
	try:
		from google import genai
	except ImportError as exc:
		raise SystemExit(
			"Missing dependency: google-genai. Install it with: pip install -r requirements.txt"
		) from exc

	if load_dotenv:
		# load .env from project root
		load_dotenv()

	api_key = os.getenv("GEMINI_API_KEY")
	if not api_key:
		error_panel = Panel(
			"[bold red]Configuration Error[/bold red]\n\nThe GEMINI_API_KEY environment variable is not configured. Please create a [bold].env[/bold] file in the project root with your API key and try again.",
			title="[red]Error[/red]",
			border_style="red"
		)
		console.print(error_panel)
		raise SystemExit(1)

	return genai.Client(api_key=api_key)


def main() -> int:
	client = build_client()
	model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
	chat = client.chats.create(model=model_name)

	# Display welcome banner
	welcome_text = Text()
	welcome_text.append("Gemini AI Chat Interface", style="bold cyan")
	welcome_text.append(f"\nModel: ", style="dim")
	welcome_text.append(model_name, style="bold green")

	welcome_panel = Panel(
		welcome_text,
		title="[cyan]Welcome[/cyan]",
		border_style="cyan",
		padding=(1, 2)
	)
	console.print(welcome_panel)

	instructions = Text()
	instructions.append("Enter your message and press ", style="dim")
	instructions.append("Enter", style="bold")
	instructions.append(". Type ", style="dim")
	instructions.append("exit", style="bold yellow")
	instructions.append(" or ", style="dim")
	instructions.append("quit", style="bold yellow")
	instructions.append(" to exit.", style="dim")
	console.print(Align.center(instructions))
	console.print()

	while True:
		try:
			user_text = console.input("[bold cyan]You:[/bold cyan] ").strip()
		except (KeyboardInterrupt, EOFError):
			console.print("\n[dim]Session ended.[/dim]")
			break

		if not user_text:
			continue

		if user_text.lower() in {"exit", "quit"}:
			console.print("[dim]Thank you for using Gemini Chat. Goodbye.[/dim]")
			break

		try:
			console.print("[dim]Processing...[/dim]")
			response = chat.send_message(user_text)
		except Exception as exc:
			error_text = Text()
			error_text.append("An error occurred: ", style="bold red")
			error_text.append(str(exc), style="red")
			error_panel = Panel(
				error_text,
				title="[red]Error[/red]",
				border_style="red"
			)
			console.print(error_panel)
			continue

		# response may be more complex depending on SDK version
		text = getattr(response, "text", None) or str(response)
	
		gemini_text = Text(text, style="green")
		gemini_panel = Panel(
			gemini_text,
			title="[bold green]Gemini[/bold green]",
			border_style="green",
			padding=(1, 2)
		)
		console.print(gemini_panel)
		console.print()

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
