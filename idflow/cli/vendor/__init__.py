import typer
from .copy import copy_vendor

app = typer.Typer(add_completion=False)
app.command("copy")(copy_vendor)

# Usage:
# ===
# # 1) interactive selection of a source
# idflow vendor copy
#
# # 2) copy all allowed directories to the current project
# idflow vendor copy --all
#
# # 3) to another target directory
# idflow vendor copy --dest ./my-project
# When copying, you will be asked for each existing file:
# O → overwrite
# S → skip
# A → abort entire operation

# Story Desc
# create another cli folder for something like sync/vendor/copy (or better suggestion?) to copy files from the pip folder to the directory where `idflow` is called (to make project-specific changes).
#
# E.g. pipelines, tasks, prompts are delivered with the pip folder.
#
# These are then used by the configuration in the project directory.
#
# If individual files are to be added for the project, these should be able to be overridden by FS structure equality in the project.
#
# In the cli command, a constant should be defined in which the directories are listed that can be copied to the local project.
#
# Z.B.
# tasks/
# templates/researcher
# templates/enricher
# templates/generator
#
# Through this definition I want to prevent that simply "all" templates have to be taken (like with tasks), but go into a possible finer-grained structure.
#
# The new CLI command should either have "--all" as a parameter (then all directories are copied), or not, then the possible directories should be displayed numbered, so that the user can specify the number for a folder via prompt to copy the desired folder to the project directory.
#
# If files already exist, each file should be asked whether to overwrite or abort.

