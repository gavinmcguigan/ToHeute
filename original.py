#!/usr/bin/sudo /home/gavin/bin/.venv/bin/python
from __future__ import annotations

import argparse
import sys
import subprocess
import os
from subprocess import run

from rich import print
from rich.console import Console
from rich.prompt import Prompt

print(sys.executable)


import git
from git import InvalidGitRepositoryError
from git import GitConfigParser

parser = argparse.ArgumentParser()
parser.add_argument("--dry", help="run the script without copying the files.", action="store_true")
args = parser.parse_args()


console = Console()

def get_copy_option(site: str, committed_files: int):
    print(f"1. Copy {committed_files} committed files to {site}")
    print(f"2. Copy {committed_files} files to {site} local to create an mkp.")
    print("\n")
    return Prompt.ask("What do you want to do?", choices=["1", "2", "q"])


def get_site() -> str:
    cmd_output = subprocess.check_output(["omd", "sites"]).decode("utf-8")
    sites = [site.split(" ")[0] for site in [site_str for site_str in cmd_output.split("\n") if site_str]] + ["quit"]
    
    print("\nSites")
    print("="*20)
    for n, site in enumerate(sites, 1):
        print(f"{n:<3}{site}")
    print("")
    choice = Prompt.ask("First, select a site", choices=[str(n) for n, _ in enumerate(sites, 1)])
    chosen_site = sites[int(choice) - 1]
    os.environ["CURRENT_SITE"] = chosen_site
    return chosen_site


def setup(gitmgr: GitMgr, site: str):
    user_choice = get_copy_option(site, gitmgr.committed_file_count)
    print("\n")
    if user_choice == "1":
        gitmgr.copy_files_to_site()
    elif user_choice == "2":
        gitmgr.copy_files_to_local_create_mkp()
    else:
        print("bye!")
    
        

class GitMgr:
    def __init__(self, site: str) -> None:
        self.site = site
        self.repo = git.Repo(search_parent_directories=True)
        config: GitConfigParser = self.repo.config_reader()
        print(config)
        self.git_username = config.get_value(section="user", option="name", default="GAV")
        print(self.git_username)
        self.last_commit_username = self.repo.head.commit.author.name
        self.your_commit = self.git_username == self.last_commit_username
        self.changed_files = [f for f, _ in self.repo.head.commit.stats.files.items() if not f.startswith((".werks", "bin"))]
        # print(self.repo.head.commit.stats.files.items())
        self.welcome_msg()
    
    def welcome_msg(self) -> None:
        print(f"\n[green]Welcome {self.git_username}[/green]\n")
        c_ok = "bold green" if self.your_commit else "bold red"        
        print(f"[{c_ok}]Last commit: {self.last_commit_username}\t{self.last_commit_time():}\t{self.last_commit_msg():.>30}[/{c_ok}]")

    def simple(self) -> None:
        for pth, _ in self.changed_files.items():
            if not pth.startswith(".werks"):
                run(["sudo", "cp", "-R", "--parents", pth, self.where], check=False)

    def pretty(self, where: str) -> None:
        with console.status("[bold green]Copying files...", spinner="monkey"):                   
            for pth in self.changed_files:
                if "Pipfile" in pth:
                    print(f"ignoring -> {pth}")
                    continue
                
                # print(f"your_commit={self.your_commit}")
                if not args.dry and self.your_commit:
                    print("Copying...", end=" ")
                    run(["sudo", "cp", "-R", "--parents", pth, where], check=False)
                else:
                    # print("copy anyway?")
                    # choice = Prompt.ask("Not your commit. Copy anyway?", choices=["y", "n"])
                    # if choice != "y":
                    #     print("Would have copied...", end=" ")
                    # else:
                    run(["sudo", "cp", "-R", "--parents", pth, where], check=False)

                print(f"{pth} -> {where}")
                
    def copy_files_to_site(self) -> None:
        self.pretty(self.f12_dir)
    
    def copy_files_to_local_create_mkp(self) -> None:
        self.pretty(self.mkp_dir)
    
    def remove_files(self) -> None:
        with console.status("[bold green]Copying files...", spinner="monkey"):
            for pth in self.changed_files:
                local_pth = self.where + "/" + pth
                print(local_pth)
                # run(["sudo", "rm", local_pth], check=False)
        
    def last_commit_time(self):
        datetime = self.repo.head.commit.committed_datetime
        return datetime.strftime("%d/%m/%Y, %H:%M:%S")
    
    def last_commit_msg(self):
        return self.repo.head.commit.message

    @property
    def committed_file_count(self) -> int:
        return len(self.changed_files)
    
    @property
    def f12_dir(self) -> str:
        return f"/omd/sites/{self.site}/lib/python3"
    
    @property
    def mkp_dir(self) -> str:
        return f"/omd/sites/{self.site}/local/lib/python3"


def main():
    site = get_site()
    if site == "quit":
        return
    try:
        gitmgr = GitMgr(site)
    except InvalidGitRepositoryError:
        console.print("\nYou're not in a git repository.", style="red")
    else:
        setup(gitmgr, site)

if __name__ == "__main__":
    main()
