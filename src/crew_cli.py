"""OpenCrew CLI - Multi-agent crew interface"""

import click
import asyncio
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt

from config.settings import settings
from src.agents.orchestrator import Orchestrator
from src.agents.crew_session import CrewSession

console = Console()


@click.group()
def cli():
    """🚀 OpenCrew - Multi-Agent AI Crew"""
    pass


@cli.command()
@click.argument("task")
@click.option("--stream", is_flag=True, help="Stream progress updates")
@click.option("--skills", default=None, help="Comma-separated list of skills to use")
def run(task: str, stream: bool, skills: str):
    """Run a task through the multi-agent crew

    Example: opencrew run "Design a scalable API for user management"
    """
    skill_list = [s.strip() for s in skills.split(",")] if skills else None

    async def execute():
        console.print(Panel(f"🚀 OpenCrew Task: {task}", style="bold green"))

        orchestrator = Orchestrator()
        crew_session = CrewSession()
        await crew_session.initialize()
        await orchestrator.initialize(skill_list)

        # Start session tracking
        session = await crew_session.start_session(
            task=task,
            num_agents=len(orchestrator.specialists) + 1,  # +1 for supervisor
        )

        start_time = datetime.now()

        try:
            if stream:
                # Stream progress
                last_update = {"message": "", "stage": ""}

                async def on_progress(update):
                    msg = f"[{update['stage'].upper()}] {update['message']}"
                    if msg != last_update["message"]:
                        console.print(msg)
                        last_update.update(update)

                orchestrator.on_progress(on_progress)

                result = await orchestrator.run(task, stream=True)
            else:
                console.print("[blue]⚙️  Crew is working... (use --stream for live progress)[/blue]")
                with console.status("[bold blue]Crew is working...", spinner="dots"):
                    result = await orchestrator.run(task, stream=False)

            elapsed = (datetime.now() - start_time).total_seconds()

            # Complete session
            await crew_session.complete_session(
                result=result,
                elapsed=elapsed,
            )

            # Display result
            console.print()
            console.print(Panel(
                Markdown(result),
                title="✅ Crew Result",
                style="bold purple",
            ))

            # Session summary
            elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed >= 60 else f"{elapsed:.1f}s"
            console.print(Panel(
                f"⏱️  Elapsed: {elapsed_str}\n"
                f"🤖 Agents: {len(orchestrator.specialists) + 1}\n"
                f"📋 Subtasks: {len(orchestrator.supervisor.current_plan.subtasks) if orchestrator.supervisor.current_plan else 0}",
                title="📊 Session Summary",
                style="cyan",
            ))

        except Exception as e:
            await crew_session.fail_session(str(e), (datetime.now() - start_time).total_seconds())
            console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))
        finally:
            await orchestrator.shutdown()

    asyncio.run(execute())


@cli.command()
@click.option("--live", is_flag=True, help="Show live dashboard (if session running)")
def vision(live: bool):
    """Show the crew vision dashboard - high-level status of all agents"""
    async def show_vision():
        orchestrator = Orchestrator()
        await orchestrator.initialize()

        vision = await orchestrator.get_vision()

        # Build dashboard
        # Header
        header = Panel(
            Text("🚀 OpenCrew Vision Dashboard", style="bold green"),
            style="green",
        )

        # Agent status table
        agent_table = Table(title="🤖 Agent Status", show_header=True)
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("Role", style="yellow")
        agent_table.add_column("Status", style="green")
        agent_table.add_column("Current Task", style="white")
        agent_table.add_column("Progress", style="magenta")

        for agent in vision.get("agent_details", []):
            status_emoji = {
                "idle": "⏸️",
                "working": "⚡",
                "done": "✅",
                "blocked": "🚫",
                "error": "❌",
                "offline": "🔌",
            }.get(agent["status"], "❓")

            progress = agent.get("progress", 0)
            progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))

            agent_table.add_row(
                agent["name"],
                agent["role"],
                f"{status_emoji} {agent['status']}",
                agent["current_task"][:40] if agent.get("current_task") else "Idle",
                f"{progress_bar} {progress:.0f}%",
            )

        # Task board
        task_table = Table(title="📋 Task Board", show_header=True)
        task_table.add_column("Task", style="cyan")
        task_table.add_column("Agent", style="yellow")
        task_table.add_column("Status", style="green")
        task_table.add_column("Progress", style="magenta")

        for task in vision.get("task_board", []):
            status_emoji = {
                "pending": "⏳",
                "assigned": "📤",
                "working": "⚡",
                "completed": "✅",
                "failed": "❌",
                "blocked": "🚫",
            }.get(task["status"], "❓")

            task_table.add_row(
                task["description"][:50],
                task["agent"][:20],
                f"{status_emoji} {task['status']}",
                f"{task['progress']:.0f}%",
            )

        # Plan info
        plan_info = ""
        if vision.get("plan"):
            plan = vision["plan"]
            plan_info = (
                f"📝 Plan: {plan.get('original_task', 'N/A')[:100]}\n"
                f"💡 Approach: {plan.get('reasoning', 'N/A')[:200]}"
            )

        # Footer
        footer = Panel(
            Text(plan_info or "No active plan", style="dim"),
            style="dim",
        )

        console.print(header)
        console.print()
        console.print(agent_table)
        console.print()
        console.print(task_table)
        console.print()
        console.print(footer)

        await orchestrator.shutdown()

    asyncio.run(show_vision())


@cli.command()
def status():
    """Quick status of the crew"""
    async def show_status():
        orchestrator = Orchestrator()
        await orchestrator.initialize()

        crew_status = await orchestrator.get_status()

        table = Table(title="🚀 OpenCrew Status")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Tasks Done", style="yellow")

        # Supervisor
        sup = crew_status.get("supervisor", {})
        table.add_row(
            "Supervisor",
            sup.get("status", "unknown"),
            str(sup.get("completed_results", 0)),
        )

        # Specialists
        for name, spec in crew_status.get("specialists", {}).items():
            table.add_row(
                f"{name.capitalize()} Agent",
                spec.get("status", "unknown"),
                str(spec.get("tasks_completed", 0)),
            )

        console.print(table)

        await orchestrator.shutdown()

    asyncio.run(show_status())


@cli.command()
@click.option("--limit", default=5, help="Number of recent sessions to show")
def history(limit: int):
    """View crew session history"""
    async def show_history():
        crew_session = CrewSession()
        sessions = await crew_session.get_recent_sessions(limit)

        if not sessions:
            console.print(Panel("No sessions found", style="yellow"))
            return

        table = Table(title="📜 Session History")
        table.add_column("#", style="cyan")
        table.add_column("Task", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Agents", style="white")
        table.add_column("Elapsed", style="magenta")
        table.add_column("Started", style="dim")

        for i, session in enumerate(sessions, 1):
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "running": "⚡",
                "cancelled": "🚫",
            }.get(session.status, "❓")

            elapsed = session.elapsed_seconds
            elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed >= 60 else f"{elapsed:.1f}s"

            started = session.started_at[:19] if session.started_at else "N/A"

            table.add_row(
                str(i),
                session.task[:50] + ("..." if len(session.task) > 50 else ""),
                f"{status_emoji} {session.status}",
                str(session.num_agents),
                elapsed_str,
                started,
            )

        console.print(table)

    asyncio.run(show_history())


@cli.command()
def stats():
    """View crew usage statistics"""
    async def show_stats():
        crew_session = CrewSession()
        stats = await crew_session.get_session_stats()

        console.print(Panel(
            f"📊 Crew Statistics\n\n"
            f"Total Sessions: {stats['total_sessions']}\n"
            f"Completed: {stats['completed']}\n"
            f"Failed: {stats['failed']}\n"
            f"Success Rate: {stats['success_rate']:.1f}%\n"
            f"Avg Elapsed: {stats['avg_elapsed_seconds']:.1f}s\n"
            f"Total Subtasks: {stats['total_subtasks']}\n"
            f"Subtasks Completed: {stats['total_completed_subtasks']}\n"
            f"Subtasks Failed: {stats['total_failed_subtasks']}",
            style="bold blue",
        ))

    asyncio.run(show_stats())


if __name__ == "__main__":
    cli()
