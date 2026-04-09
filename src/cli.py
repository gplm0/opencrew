import click
import asyncio
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from datetime import datetime
import json
import websockets

console = Console()

API_URL = "http://localhost:3000"


@click.group()
def cli():
    """🤖 Jarvis AI Assistant - CLI Interface"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=3000, help="Port to bind")
def serve(host, port):
    """Start the Jarvis API server"""
    import uvicorn
    from src.api.server import app
    
    console.print(Panel("🚀 Starting Jarvis API Server...", style="bold green"))
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.option("--skill", default=None, help="Use a specific skill")
@click.option("--user-id", default="cli-user", help="User ID")
def chat(skill, user_id):
    """Chat with Jarvis"""
    console.print(Panel(
        "🤖 Jarvis AI Assistant\n"
        "Type your message or /quit to exit\n"
        "Use /skill <name> to switch skills",
        style="bold blue"
    ))
    
    current_skill = skill
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if user_input.lower() in ["/quit", "/exit", "q"]:
                console.print(Panel("👋 Goodbye!", style="bold yellow"))
                break
            
            if user_input.startswith("/skill "):
                current_skill = user_input.split(" ", 1)[1].strip()
                console.print(Panel(f"🛠️  Switched to /{current_skill} skill", style="cyan"))
                continue
            
            # Make request to API
            async def query():
                if current_skill:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            f"{API_URL}/skill/{current_skill}",
                            json={"input": user_input},
                        )
                        return response.json()
                else:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            f"{API_URL}/query",
                            json={"message": user_input, "user_id": user_id},
                        )
                        return response.json()
            
            with console.status("[bold blue]Jarvis is thinking...", spinner="dots"):
                result = asyncio.run(query())
            
            # Display response
            content = result.get("content", "No response")
            console.print()
            console.print(Panel(Markdown(content), title="🤖 Jarvis", style="bold purple"))
            
        except KeyboardInterrupt:
            console.print(Panel("👋 Goodbye!", style="bold yellow"))
            break
        except Exception as e:
            console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))


@cli.command()
def skills():
    """List available skills"""
    async def fetch_skills():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/skills")
            return response.json()
    
    try:
        result = asyncio.run(fetch_skills())
        
        table = Table(title="🛠️  Available Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Status", style="yellow")
        
        for skill in result.get("skills", []):
            status = "✅ Enabled" if skill["enabled"] else "❌ Disabled"
            table.add_row(
                f"/{skill['name']}",
                skill["description"],
                status,
            )
        
        console.print(table)
    except Exception as e:
        console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))


@cli.command()
@click.argument("skill_name")
@click.argument("input_text")
def use_skill(skill_name, input_text):
    """Use a specific skill"""
    async def execute_skill():
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_URL}/skill/{skill_name}",
                json={"input": input_text},
            )
            return response.json()
    
    try:
        with console.status(f"[bold blue]Using /{skill_name}...", spinner="dots"):
            result = asyncio.run(execute_skill())
        
        content = result.get("content", "No response")
        console.print(Panel(Markdown(content), title=f"🛠️  /{skill_name}", style="bold purple"))
    except Exception as e:
        console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))


@cli.command()
@click.option("--user-id", default="cli-user", help="User ID")
def history(user_id):
    """View conversation history"""
    async def fetch_history():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/history/{user_id}")
            return response.json()
    
    try:
        result = asyncio.run(fetch_history())
        
        table = Table(title="💬 Conversation History")
        table.add_column("#", style="cyan")
        table.add_column("User Message", style="green", max_width=40)
        table.add_column("Skill", style="yellow")
        table.add_column("Timestamp", style="magenta")
        
        for i, conv in enumerate(result.get("conversations", []), 1):
            table.add_row(
                str(i),
                conv["user_message"][:50] + "...",
                conv.get("skill_used", "-"),
                conv["timestamp"][:19],
            )
        
        console.print(table)
    except Exception as e:
        console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))


@cli.command()
@click.option("--user-id", default="cli-user", help="User ID")
def stats(user_id):
    """View usage statistics"""
    async def fetch_stats():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/history/{user_id}/stats")
            return response.json()
    
    try:
        result = asyncio.run(fetch_stats())
        
        console.print(Panel(
            f"📊 Usage Statistics\n\n"
            f"Total Conversations: {result['total_conversations']}\n"
            f"Input Tokens: {result['total_input_tokens']:,}\n"
            f"Output Tokens: {result['total_output_tokens']:,}\n"
            f"Total Tokens: {result['total_tokens']:,}\n"
            f"Last Activity: {result.get('last_conversation', 'N/A')}",
            style="bold blue"
        ))
    except Exception as e:
        console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))


@cli.command()
def ws():
    """Connect via WebSocket"""
    async def ws_connect():
        uri = f"ws://localhost:3000/ws/cli-ws"
        try:
            async with websockets.connect(uri) as ws:
                console.print(Panel("🔌 Connected via WebSocket", style="bold green"))
                
                async def send_messages():
                    while True:
                        msg = await asyncio.get_event_loop().run_in_executor(
                            None, input, "You: "
                        )
                        await ws.send(json.dumps({"message": msg}))
                
                async def receive_messages():
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        console.print(Panel(
                            data.get("content", ""),
                            title="🤖 Jarvis (WS)",
                            style="bold purple"
                        ))
                
                await asyncio.gather(send_messages(), receive_messages())
        except Exception as e:
            console.print(Panel(f"❌ Error: {str(e)}", style="bold red"))
    
    asyncio.run(ws_connect())


if __name__ == "__main__":
    cli()
