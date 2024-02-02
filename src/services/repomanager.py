"""
Service used to manage the local repositories.
"""

import os
import uuid
from src.my_types import Autor
from src.decorators import run_in_separate_process
import git
from git.exc import InvalidGitRepositoryError
import datetime

from src.logs import logging

class LocalRepo():
    def __init__(self, repo_path: str):
        self.repo_path: str = repo_path

        try:
            self.repo = git.Repo(repo_path)
        except InvalidGitRepositoryError:
            self.repo = None
            logging.getLogger("repomanager").error(f"Invalid git repository at {repo_path}.")

    def is_initialized(self):
        return self.repo is not None

    def pull(self):
        self.repo.remote().pull()

    def create_branch(self, branch_name: str):
        self.repo.git.checkout(b=branch_name)
        self.repo.git.push("--set-upstream", "origin", branch_name)

    def move_to_branch(self, branch_name: str):
        self.repo.git.checkout(branch_name)

    def commit_files(self, files_to_commit: list[str], autor: Autor):
        index = self.repo.index


@run_in_separate_process
def check_repo_exists(repo_path: str) -> bool:
    """Check if the repository exists in the local directory and is a valid git repository.

    Args
    ----
    repo_path: str
        Local GitHub repository path.

    """
    # first check if abs path is within project folder
    if not os.path.abspath(repo_path).startswith(os.path.abspath(os.getcwd())):
        return False
    
    if not os.path.exists(repo_path):
        return False
    
    # check if correct git repository
    try:
        git.Repo(repo_path)
    except InvalidGitRepositoryError:
        return False

    return True

@run_in_separate_process
def create_and_move_to_branch(repo_path: str, branch_name: str) -> None:
    """Move to a branch, or create it if it does not exist.

    Args
    ----
    repo_path: str
        Local GitHub repository path.
    branch_name: str
        Name of the branch to create.

    Returns
    -------
    str
        Name of the branch created.
    """
    # Initialize the repository object
    repo = git.Repo(repo_path)
    repo.remote().pull()

    # Create a new branch both locally and remotely
    repo.git.checkout(b=branch_name)
    repo.git.push("--set-upstream", "origin", branch_name)

@run_in_separate_process
def move_to_branch(repo_path: str, branch_name: str) -> None:
    """Move to a branch, or create it if it does not exist.

    Args
    ----
    repo_path: str
        Local GitHub repository path.
    branch_name: str
        Name of the branch to create.

    Returns
    -------
    str
        Name of the branch created.
    """
    repo = git.Repo(repo_path)
    repo.git.checkout(branch_name)

@run_in_separate_process
def commit_files(repo_path: str, files_to_commit: list[str], autor: Autor) -> bool:
    """Commit files to the repository.

    Args
    ----
    repo_path: str
        Local GitHub repository path.
    files_to_commit: list[str]
        List of files to commit.

    Returns
    -------
    bool
        True if the commit was successful, False otherwise.
    """
    try:
        # Initialize the repository object
        repo = git.Repo(repo_path)

        # Get the index (staging area)
        index = repo.index

        # Add files to the index
        index.add(files_to_commit)

        # Committer information

        author: git.Actor = git.Actor(autor.name, autor.email)
        escape = '\n'
        commit_message = f"""Autogenerated commit on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Of {len(files_to_commit)} files

        Names:
        {escape.join(files_to_commit)}

        by {autor.name} <{autor.email}>
        """
        index.add([files_to_commit])
        index.commit(commit_message, author=author, committer=author)

        repo.remote().push()
        logging.getLogger("repomanager").info(f"Files committed successfully to the repository {repo_path}.")

    except Exception as e:
        logging.getLogger("repomanager").error(f"Error occurred while committing files to the repository {repo_path}.")
        logging.getLogger("repomanager").error(f"Error details: {repr(e)}")
        return False

    return True

def create_branch_name(author: Autor) -> str:
    """Create a branch name based on the current date and time and the author's name.

    The format will be authorname-YYYYMMDD-HHMMSS-uuid4.
    We need the uuid4 to have the guarantee that the branch name is unique.

    Args
    ----
    author: Autor
        Author of the commit.

    Returns
    -------
    str
        Branch name.
    """

    return f"{author.name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4()}"
