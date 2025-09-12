"""
Initialize a new ID Flow project with virtual environment setup.
"""
from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import typer


def _detect_local_idflow(target_dir: Path) -> Optional[Path]:
    """
    Detect if we're in a local idflow development environment.

    Looks for:
    Parent directory containing pyproject.toml with idflow package

    Returns the path to the local idflow project if found, None otherwise.
    """
    current_path = target_dir.resolve()

    # Walk up the directory tree looking for idflow project
    for parent in [current_path] + list(current_path.parents):
        # Check for pyproject.toml with idflow package
        pyproject_file = parent / "pyproject.toml"
        if pyproject_file.exists():
            try:
                content = pyproject_file.read_text()
                if 'name = "idflow"' in content or 'name="idflow"' in content:
                    # Verify it's actually an idflow project by checking for idflow/ directory
                    idflow_dir = parent / "idflow"
                    if idflow_dir.exists() and (idflow_dir / "__init__.py").exists():
                        return parent
            except Exception:
                continue

        # # Check for setup.py with idflow package
        # setup_file = parent / "setup.py"
        # if setup_file.exists():
        #     try:
        #         content = setup_file.read_text()
        #         if 'name="idflow"' in content or "name='idflow'" in content:
        #             # Verify it's actually an idflow project
        #             idflow_dir = parent / "idflow"
        #             if idflow_dir.exists() and (idflow_dir / "__init__.py").exists():
        #                 return parent
        #     except Exception:
        #         continue

        # # Check for idflow/ directory with __init__.py (fallback)
        # idflow_dir = parent / "idflow"
        # if idflow_dir.exists() and (idflow_dir / "__init__.py").exists():
        #     # Additional check: look for typical idflow project files
        #     if ((parent / "pyproject.toml").exists() or
        #         (parent / "setup.py").exists() or
        #         (parent / "idflow" / "__main__.py").exists()):
        #         return parent

    return None


def _handle_project_launch(project_name: Optional[str], target_dir: Path, venv_name: str, launch_project: Optional[bool]):
    """
    Handle project launching after successful initialization.

    Args:
        project_name: Name of the project (None if initialized in current directory)
        target_dir: Target directory where project was initialized
        venv_name: Name of the virtual environment directory
        launch_project: Whether to launch the project (False means prompt user)
    """
    # Determine if we should launch the project
    should_launch = launch_project

    if should_launch is None:
        # Prompt user if not specified (only when neither --launch-project nor --no-launch-project was used)
        typer.echo("\n" + "="*50)
        typer.echo("🚀 Project Launch")
        typer.echo("="*50)

        if project_name:
            typer.echo(f"Project '{project_name}' has been created successfully!")
        else:
            typer.echo(f"Project initialized in current directory: {target_dir}")

        should_launch = typer.confirm("Would you like to launch the project?", default=True)

    # Determine if we should change directory (only if project_name was provided)
    change_directory = project_name is not None and should_launch

    # Generate activation commands
    if sys.platform == "win32":
        activate_cmd = f"{venv_name}\\Scripts\\activate"
    else:
        activate_cmd = f"source {venv_name}/bin/activate"

    if should_launch:
        typer.echo("\n" + "="*50)
        typer.echo("🚀 Launching Project")
        typer.echo("="*50)

        # Change directory if needed
        if change_directory:
            typer.echo(f"📁 Changing to project directory: {target_dir}")
            os.chdir(target_dir)

        typer.echo(f"🐍 Virtual environment activation command:")
        typer.echo(f"   {activate_cmd}")

        # Try to activate the virtual environment in the current shell
        try:
            if sys.platform == "win32":
                # On Windows, we can't easily activate in the current shell
                typer.echo(f"\n⚠️  On Windows, please manually run:")
                typer.echo(f"   {activate_cmd}")
            else:
                # On Unix-like systems, try to source the activation script
                typer.echo(f"\n🔄 Attempting to activate virtual environment...")

                # Check if we're in a shell that supports sourcing
                if os.environ.get('SHELL') and 'bash' in os.environ.get('SHELL', '').lower():
                    # Try to activate by modifying the current environment
                    venv_python = target_dir / venv_name / "bin" / "python"
                    if venv_python.exists():
                        # Set environment variables to simulate activation
                        os.environ['VIRTUAL_ENV'] = str(target_dir / venv_name)
                        os.environ['PATH'] = str(target_dir / venv_name / "bin") + ":" + os.environ.get('PATH', '')
                        os.environ['PS1'] = f"({project_name or 'idflow'}) " + os.environ.get('PS1', '')

                        typer.echo(f"✅ Virtual environment activated!")
                        typer.echo(f"   Python: {venv_python}")
                        typer.echo(f"   Project: {target_dir}")
                    else:
                        typer.echo(f"⚠️  Could not find Python in virtual environment")
                        typer.echo(f"   Please manually run: {activate_cmd}")
                else:
                    typer.echo(f"⚠️  Please manually run: {activate_cmd}")

        except Exception as e:
            typer.echo(f"⚠️  Could not automatically activate virtual environment: {e}")
            typer.echo(f"   Please manually run: {activate_cmd}")

        # Show next steps
        typer.echo(f"\n🎯 Next steps:")
        if project_name:
            typer.echo(f"   cd {project_name}")
        typer.echo(f"   {activate_cmd}")
        typer.echo(f"   idflow doc add 'My first document'")
        typer.echo(f"   idflow doc list")
    else:
        typer.echo(f"\n📝 Manual setup:")
        if project_name:
            typer.echo(f"   cd {project_name}")
        typer.echo(f"   {activate_cmd}")
        typer.echo(f"   idflow doc add 'My first document'")


def init_project(
    project_name: Optional[str] = typer.Argument(None, help="Project name (creates new directory or uses current directory if no project name is provided)"),
    python: str = typer.Option("python3", "--python", help="Python executable to use"),
    venv_name: str = typer.Option(".venv", "--venv", help="Virtual environment directory name"),
    add_feature: list[str] = typer.Option([], "--add-feature", help="Add feature to install (can be used multiple times)"),
    launch_project: Optional[bool] = typer.Option(None, "--launch-project/--no-launch-project", help="Whether to launch the project after initialization (prompt if not specified)")
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

        # Check if we're in a development environment (local idflow project)
        local_idflow_path = _detect_local_idflow(target_dir)

        if local_idflow_path:
            # Use local idflow installation
            typer.echo(f"🔧 Detected local idflow development environment")
            typer.echo(f"   Using local idflow from: {local_idflow_path}")

            if add_feature:
                # For local development, we can't use feature syntax
                typer.echo(f"   Note: Features {', '.join(add_feature)} will be available from local installation")

            install_cmd = [str(pip_exe), "install", "-e", str(local_idflow_path)]
        else:
            # Use PyPI installation
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
    # Create features.d and template
    features_dir = config_dir / "features.d"
    features_dir.mkdir(exist_ok=True)
    features_template = features_dir / "features.toml"
    if not features_template.exists():
        tpl = """# Project feature definitions (modular). Add more files in config/features.d/ as needed.
#
# Example feature (uncomment and adjust):
# [features.example]
# packages = [
#   "requests>=2.31.0",
#   "beautifulsoup4>=4.12.0",
#   "playwright>=1.40.0",
# ]
# extends = [
#   # "research",  # inherit from package extra or another project feature
# ]
"""
        features_template.write_text(tpl)
        typer.echo("✅ Created config/features.d/features.toml")

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

    # Create .env file for automatic venv activation
    env_file = target_dir / ".env"
    if not env_file.exists():
        if sys.platform == "win32":
            env_content = f"""# ID Flow Environment
# Automatically activate virtual environment when entering this directory
# Usage: source .env (or add to your shell profile)

# Activate virtual environment
call {venv_name}\\Scripts\\activate.bat

# Set project-specific environment variables
export IDFLOW_PROJECT_DIR="{target_dir.name}"
export IDFLOW_CONFIG_DIR="config"
export IDFLOW_DATA_DIR="data"

# Optional: Set Conductor URL
# export CONDUCTOR_SERVER_URL="http://localhost:8080"
"""
        else:
            env_content = f"""# ID Flow Environment
# Automatically activate virtual environment when entering this directory
# Usage: source .env (or add to your shell profile)

# Activate virtual environment
source {venv_name}/bin/activate

# Set project-specific environment variables
export IDFLOW_PROJECT_DIR="{target_dir.name}"
export IDFLOW_CONFIG_DIR="config"
export IDFLOW_DATA_DIR="data"

# Optional: Set Conductor URL
# export CONDUCTOR_SERVER_URL="http://localhost:8080"
"""
        env_file.write_text(env_content)
        typer.echo("✅ Created .env")

    # Success message
    typer.echo("\n🎉 Project initialized successfully!")
    typer.echo(f"\nNext steps:")
    typer.echo(f"- Activate the virtual environment:")
    if sys.platform == "win32":
        typer.echo(f"   {venv_name}\\Scripts\\activate")
    else:
        typer.echo(f"   source {venv_name}/bin/activate")

    typer.echo(f"   Or use: source .env")

    if project_name:
        typer.echo(f"\n- Project created in: {target_dir}")
        typer.echo(f"To get started, run: cd {project_name}")


    typer.echo(f"\n- Quick start with automatic venv activation:")
    typer.echo(f"   source .env  # Activates venv and sets environment variables")
    typer.echo(f"   idflow doc add 'My first document'")
    typer.echo(f"   idflow doc list")

    # Handle project launching
    _handle_project_launch(project_name, target_dir, venv_name, launch_project)


def main():
    """Main entry point for the init command."""
    typer.run(init_project)


if __name__ == "__main__":
    main()
