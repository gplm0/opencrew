import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from config.settings import settings
from src.brain.llm import QwenLLM
from src.brain.waza_skills import WazaSkillsManager, WazaSkillRequest

console = Console()


async def main():
    console.print(Panel(
        "🤖 Jarvis AI Assistant - Direct CLI\n"
        "No server needed - talking directly to qwen3.5:cloud\n"
        "Type your message or /quit to exit\n"
        "Use /skill <name> to switch skills",
        style="bold blue"
    ))

    # Initialize LLM
    llm = QwenLLM(
        api_type=settings.QWEN_API_TYPE,
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=settings.TEMPERATURE,
        top_p=settings.TOP_P,
        max_tokens=settings.MAX_TOKENS,
    )

    # Initialize Waza Skills
    waza = WazaSkillsManager(llm)

    console.print(f"[green]✓[/green] Loaded model: {settings.OLLAMA_MODEL}")
    console.print(f"[green]✓[/green] Available skills: {', '.join(waza.get_available_skills())}\n")

    current_skill = None

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")

            if user_input.lower() in ["/quit", "/exit", "q"]:
                console.print(Panel("👋 Goodbye!", style="bold yellow"))
                break

            if user_input.startswith("/skill "):
                current_skill = user_input.split(" ", 1)[1].strip()
                if current_skill:
                    console.print(Panel(f"🛠️  Switched to /{current_skill} skill", style="cyan"))
                else:
                    current_skill = None
                    console.print(Panel("🛠️  Cleared skill - using general mode", style="cyan"))
                continue

            with console.status("[bold blue]Jarvis is thinking...", spinner="dots"):
                try:
                    if current_skill:
                        response = await waza.execute_skill(
                            WazaSkillRequest(skill=current_skill, input=user_input)
                        )
                        content = response.content
                    else:
                        response = await llm.query(user_input)
                        content = response.content

                    console.print()
                    console.print(Panel(Markdown(content), title="🤖 Jarvis", style="bold purple"))
                except Exception as e:
                    console.print(Panel(f"❌ LLM Error: {str(e)}", style="bold red"))

        except KeyboardInterrupt:
            console.print(Panel("👋 Goodbye!", style="bold yellow"))
            break
        except Exception as e:
            console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))


if __name__ == "__main__":
    asyncio.run(main())
