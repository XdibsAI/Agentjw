#!/usr/bin/env python3
"""
main.py - AgentJW Entry Point

Usage:
    python main.py                    # Start interactive CLI (chat mode)
    python main.py build <task>       # Direct build mode
    python main.py chat <message>     # Single chat message
    python main.py status             # Show status
    python main.py --help             # Show help
"""
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_environment():
    """Validate environment before starting"""
    from pathlib import Path

    env_file = Path(".env")
    if not env_file.exists():
        example = Path(".env.example")
        if example.exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("⚠️  Created .env from .env.example")
            print("   Please edit .env and add your API key!")
            print("   Then run: python main.py")
            sys.exit(1)

    from core.config import config
    if not config.get_llm_key() or config.get_llm_key().startswith("sk-your"):
        print("❌ ERROR: No API key configured!")
        print(f"   Edit .env and set {'OPENAI_API_KEY' if config.LLM_PROVIDER == 'openai' else 'ANTHROPIC_API_KEY'}")
        print(f"   Current provider: {config.LLM_PROVIDER}")
        sys.exit(1)

    config.ensure_dirs()


def main():
    args = sys.argv[1:]

    # Handle direct commands without initializing full system
    if not args:
        # Interactive mode
        check_environment()
        from interface.cli import CLI
        cli = CLI()
        cli.run()

    elif args[0] == "--help" or args[0] == "-h":
        print(__doc__)
        sys.exit(0)

    elif args[0] == "build" and len(args) > 1:
        check_environment()
        task = " ".join(args[1:])
        from core.logger import console
        from agents.orchestrator import orchestrator
        import uuid
        console.print(f"[cyan]Building: {task}[/cyan]")
        orchestrator.build(task, str(uuid.uuid4()))

    elif args[0] == "chat" and len(args) > 1:
        check_environment()
        message = " ".join(args[1:])
        from agents.orchestrator import orchestrator
        from core.logger import console
        import uuid
        response = orchestrator.chat(message, [], str(uuid.uuid4()))
        console.print(response)

    elif args[0] == "status":
        try:
            check_environment()
        except SystemExit:
            pass
        from core.config import config
        print(f"Provider : {config.LLM_PROVIDER}")
        print(f"Model    : {config.get_model()}")
        print(f"Projects : {config.PROJECTS_DIR}")
        print(f"Memory   : {config.SQLITE_PATH}")

    else:
        # Treat unknown args as a chat message or build task
        check_environment()
        message = " ".join(args)
        from agents.orchestrator import orchestrator
        from core.logger import console
        import uuid
        response = orchestrator.chat(message, [], str(uuid.uuid4()))
        console.print(response)


if __name__ == "__main__":
    main()
