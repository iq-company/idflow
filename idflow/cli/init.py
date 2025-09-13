"""
Initialize a new ID Flow project with virtual environment setup.
"""
from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import shutil
import importlib.resources as ir
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

        # Launch an interactive subshell inside the project with venv activated
        try:
            if sys.platform == "win32":
                # Replace current process with cmd.exe session
                cmd_exe = os.environ.get("COMSPEC", "cmd.exe")
                cmd = f"cd /d \"{str(target_dir)}\" && call \"{venv_name}\\\\Scripts\\\\activate.bat\" && title idflow:{project_name or target_dir.name}"
                typer.echo("\n🔁 Starting interactive cmd with activated venv (exit to return)...")
                os.execv(cmd_exe, [cmd_exe, "/K", cmd])
            else:
                shell = os.environ.get("SHELL", "/bin/bash")
                venv_dir = (target_dir / venv_name).resolve()
                venv_bin = (venv_dir / "bin").resolve()
                # Prepare environment for the new shell
                env = os.environ.copy()
                env["VIRTUAL_ENV"] = str(venv_dir)
                env["PATH"] = f"{str(venv_bin)}:" + env.get("PATH", "")
                if "PS1" in env:
                    env["PS1"] = f"({project_name or target_dir.name}) " + env["PS1"]
                else:
                    env["PS1"] = f"({project_name or target_dir.name}) $ "
                # Change to project directory and exec interactive shell
                os.chdir(target_dir)
                typer.echo("\n🔁 Starte interaktive Shell mit aktivierter venv (exit zum Beenden)...")
                os.execve(shell, [shell, "-i"], env)
        except Exception as e:
            typer.echo(f"⚠️  Konnte interaktive Shell nicht starten: {e}")
            typer.echo(f"   Bitte manuell ausführen: cd {target_dir} && {activate_cmd}")

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
    add_extra: list[str] = typer.Option([], "--add-extra", help="Add extra to install (can be used multiple times)"),
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

            if add_extra:
                # For local development, we can't use extras syntax
                typer.echo(f"   Note: Extras {', '.join(add_extra)} will be available from local installation")

            install_cmd = [str(pip_exe), "install", "-e", str(local_idflow_path)]
        else:
            # Use PyPI installation
            if add_extra:
                # Create extras string like "research,writer"
                extras_str = ",".join(add_extra)
                install_cmd = [str(pip_exe), "install", f"idflow[{extras_str}]"]
                typer.echo(f"Installing idflow with extras: {', '.join(add_extra)}")
            else:
                install_cmd = [str(pip_exe), "install", "idflow"]
                typer.echo("Installing idflow (base)")

        subprocess.run(install_cmd, check=True)
        typer.echo("✅ idflow installed successfully")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error installing idflow: {e}")
        raise typer.Exit(1)

    # Create project structure from template directory
    typer.echo("Creating project structure from template...")

    template_root = ir.files("idflow") / "templates" / "project"
    try:
        # materialize resource to filesystem if needed and copy recursively
        with ir.as_file(template_root) as src_path:
            # Copy without overwriting existing files
            for root, dirs, files in os.walk(src_path):
                rel = Path(root).relative_to(src_path)
                dest_dir = target_dir / rel
                dest_dir.mkdir(parents=True, exist_ok=True)
                for name in files:
                    src_file = Path(root) / name
                    dest_file = dest_dir / name
                    if not dest_file.exists():
                        shutil.copy2(src_file, dest_file)
    except Exception as e:
        typer.echo(f"Error copying project template: {e}")
        raise typer.Exit(1)

    # Replace placeholders in templated files
    project_display_name = project_name or target_dir.name
    replacements = {
        "__PROJECT_NAME__": project_display_name,
        "__VENV_NAME__": venv_name,
    }

    for rel in [
        "pyproject.toml",
        "README.md",
        ".env",
        ".env.bat",
        "config/idflow.yml",
    ]:
        fpath = target_dir / rel
        if fpath.exists():
            try:
                content = fpath.read_text()
                for k, v in replacements.items():
                    content = content.replace(k, v)
                fpath.write_text(content)
            except Exception:
                # Best-effort; continue without failing the init
                pass

    # Ensure data directories exist (template also contains .gitkeep)
    (target_dir / "data" / "inbox").mkdir(parents=True, exist_ok=True)
    (target_dir / "data" / "active").mkdir(parents=True, exist_ok=True)
    (target_dir / "data" / "done").mkdir(parents=True, exist_ok=True)

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
