"""
Initialize a new ID Flow project with virtual environment setup.
"""
from __future__ import annotations
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional
import typer


def init_project(
    project_name: Optional[str] = typer.Argument(None, help="Project name (creates new directory or uses current directory if no project name is provided)"),
    python: str = typer.Option("python3", "--python", help="Python executable to use"),
    venv_name: str = typer.Option(".venv", "--venv", help="Virtual environment directory name"),
    add_feature: list[str] = typer.Option([], "--add-feature", help="Add feature to install (can be used multiple times)")
):
    """
    Initialize a new ID Flow project.

    If project_name is provided, creates a new directory and sets up the project there.
    If no project_name is provided, initializes the current directory.
    """
    current_dir = Path.cwd()

    if project_name:
        # Create new project directory
        project_dir = current_dir / project_name

        if project_dir.exists():
            typer.echo(f"Error: Directory '{project_name}' already exists")
            raise typer.Exit(1)

        typer.echo(f"Creating project directory: {project_dir}")
        project_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(project_dir)
        target_dir = project_dir
    else:
        # Use current directory
        target_dir = current_dir
        typer.echo(f"Initializing project in current directory: {target_dir}")

    # Check if we're in an empty directory (except for .venv)
    existing_files = [f for f in target_dir.iterdir() if f.name != venv_name]
    if existing_files:
        typer.echo(f"Error: You're not in an empty directory. Found: {[f.name for f in existing_files]}")
        typer.echo("Please run 'idflow init' in an empty directory or use 'idflow init <project_name>' to create a new project.")
        raise typer.Exit(1)

    # Create virtual environment
    venv_path = target_dir / venv_name

    # Check if it's a valid virtual environment
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    if venv_path.exists() and python_exe.exists():
        typer.echo(f"Using existing virtual environment: {venv_path}")
    else:
        if venv_path.exists():
            typer.echo(f"Removing invalid virtual environment: {venv_path}")
            import shutil
            shutil.rmtree(venv_path)

        typer.echo(f"Creating virtual environment: {venv_path}")
        try:
            subprocess.run([python, "-m", "venv", str(venv_path)], check=True)
        except subprocess.CalledProcessError as e:
            typer.echo(f"Error creating virtual environment: {e}")
            raise typer.Exit(1)
        except FileNotFoundError:
            typer.echo(f"Error: Python executable '{python}' not found")
            raise typer.Exit(1)

    # Determine activation script path
    if sys.platform == "win32":
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_exe = venv_path / "Scripts" / "pip.exe"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        pip_exe = venv_path / "bin" / "pip"
        python_exe = venv_path / "bin" / "python"

    # Install idflow in virtual environment
    typer.echo("Installing idflow in virtual environment...")
    try:
        # Upgrade pip first
        subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)

        # Install idflow with features
        if add_feature:
            # Create feature string like "research,writer"
            features_str = ",".join(add_feature)
            install_cmd = [str(pip_exe), "install", f"idflow[{features_str}]"]
            typer.echo(f"Installing idflow with features: {', '.join(add_feature)}")
        else:
            install_cmd = [str(pip_exe), "install", "idflow"]
            typer.echo("Installing idflow (base)")

        subprocess.run(install_cmd, check=True)
        typer.echo("✅ idflow installed successfully")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error installing idflow: {e}")
        raise typer.Exit(1)

    # Create basic project structure
    typer.echo("Creating project structure...")

    # Create data directories
    (target_dir / "data" / "inbox").mkdir(parents=True, exist_ok=True)
    (target_dir / "data" / "active").mkdir(parents=True, exist_ok=True)
    (target_dir / "data" / "done").mkdir(parents=True, exist_ok=True)

    # Create config directory
    config_dir = target_dir / "config"
    config_dir.mkdir(exist_ok=True)

    # Create basic config file if it doesn't exist
    config_file = config_dir / "idflow.yml"
    if not config_file.exists():
        config_content = f"""# ID Flow Configuration
base_dir: "data"
config_dir: "config"
document_implementation: "fs_markdown"
conductor_server_url: "http://localhost:8080"
"""
        config_file.write_text(config_content)
        typer.echo("✅ Created config/idflow.yml")

    # Create .gitignore
    gitignore_file = target_dir / ".gitignore"
    if not gitignore_file.exists():
        gitignore_content = """# ID Flow
data/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        gitignore_file.write_text(gitignore_content)
        typer.echo("✅ Created .gitignore")

    # Success message
    typer.echo("\n🎉 Project initialized successfully!")
    typer.echo(f"\nNext steps:")
    typer.echo(f"- Activate the virtual environment:")
    if sys.platform == "win32":
        typer.echo(f"   {venv_name}\\Scripts\\activate")
    else:
        typer.echo(f"   source {venv_name}/bin/activate")

    if project_name:
        typer.echo(f"\n- Project created in: {target_dir}")
        typer.echo(f"To get started, run: cd {project_name}")

    typer.echo(f"- Start using idflow:")
    typer.echo(f"   idflow doc add 'My first document'")
    typer.echo(f"   idflow doc list")


def main():
    """Main entry point for the init command."""
    typer.run(init_project)


if __name__ == "__main__":
    main()
