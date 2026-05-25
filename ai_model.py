from __future__ import annotations

import os
import sys

try:
	from dotenv import load_dotenv
except Exception:
	load_dotenv = None


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
		raise SystemExit(
			"GEMINI_API_KEY is not set. Create a .env file with GEMINI_API_KEY and try again."
		)

	return genai.Client(api_key=api_key)


def main() -> int:
	client = build_client()
	model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
	chat = client.chats.create(model=model_name)

	print(f"Gemini chat ready using {model_name}.")
	print('Type your message and press Enter. Type "exit" or "quit" to stop.')

	while True:
		try:
			user_text = input("Ask Gemini: ").strip()
		except (KeyboardInterrupt, EOFError):
			print()
			break

		if not user_text:
			continue

		if user_text.lower() in {"exit", "quit"}:
			break

		try:
			response = chat.send_message(user_text)
		except Exception as exc:
			print(f"Error: {exc}", file=sys.stderr)
			continue

		# response may be more complex depending on SDK version
		text = getattr(response, "text", None) or str(response)
		print(f"Gemini: {text}\n")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
