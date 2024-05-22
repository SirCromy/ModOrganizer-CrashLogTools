import os
import re
from typing import (Callable, Dict, List)

from dulwich import porcelain as git

from . import addresslib

STACK_PATTERN = re.compile(
    r"(\t\[ *\d+\] 0x[0-9A-F]+ .*\+[0-9A-F]+) -> (?P<id>\d+)\+0x[0-9A-F]+")

class CrashLogProcessor():
    def __init__(self, game : str, delete_callback : Callable[[str], None]):
        self.database = addresslib.get_database(game)
        self.git_repo = os.path.join(os.path.dirname(__file__), game)
        self.delete_callback = delete_callback

    def clone_database(self) -> None:
        if not os.path.exists(self.git_repo):
            try:
                git.clone(
                    self.database.remote,
                    self.git_repo,
                    branch=self.database.branch)
            except git.Error:
                pass

    def update_database(self) -> None:
        self.clone_database()
        try:
            git.pull(self.git_repo, self.database.remote)
            if git.active_branch(self.git_repo) != self.database.branch:
                git.checkout(self.git_repo, self.database.branch)
        except git.Error:
            pass

    def get_database_path(self) -> str:
        return os.path.join(self.git_repo, self.database.database_file)

    def process_log(self, log : str) -> None:
        crash_log = CrashLog(log)

        addr_ids = set()
        width = 0
        for line in crash_log.call_stack:
            match = STACK_PATTERN.match(line)
            if not match:
                continue
            addr_ids.add(int(match.group("id")))
            width = max(width, len(match.group(0)) + 1)

        if not addr_ids:
            return
        id_list = sorted(addr_ids)

        id_lookup = self.lookup_ids(id_list)
        if not id_lookup:
            return

        crash_log.rewrite_call_stack(lambda line : self.add_name(line, id_lookup, width))
        if crash_log.changed:
            self.delete_callback(log)
            crash_log.write_file(log)

    def add_name(self, line : str, id_lookup : Dict[int, str], width : int) -> str:
        match = STACKTo fully update the Mod Organizer plugins for Skyrim crash logs to use PyQt6, you should follow these detailed steps for each relevant file:

### Step-by-Step Solution

1. **Replace PyQt5 with PyQt6 Imports:**
   Update all `PyQt5` imports to `PyQt6` in your files.
   
2. **Adjust Code for PyQt6:**
   Update any class and method names that have changed between PyQt5 and PyQt6.

### File Updates

#### `crashloglabeler.py`

```python
from typing import *
from mobase import *
if TYPE_CHECKING:
    from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import *

from .crashlogutil import CrashLogProcessor
from . import crashlogs
from . import addresslib

class CrashLogLabeler(IPlugin):

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        return "Crash Log Labeler"

    def version(self) -> "VersionInfo":
        return VersionInfo(1, 0, 1, 0, ReleaseType.FINAL)

    def description(self) -> str:
        return "Labels known addresses in Skyrim crash logs"

    def author(self) -> str:
        return "Parapets"

    def requirements(self) -> List["IPluginRequirement"]:
        games = set.intersection(
            addresslib.supported_games(),
            crashlogs.supported_games()
        )

        return [
            PluginRequirementFactory.gameDependency(games)
        ]

    def settings(self) -> List["PluginSetting"]:
        return [
            PluginSetting(
                "offline_mode",
                "Disable update from remote database",
                False
            ),
        ]

    def init(self, organizer : "IOrganizer") -> bool:
        self.organizer = organizer
        organizer.onFinishedRun(self.onFinishedRunCallback)
        organizer.onUserInterfaceInitialized(self.onUserInterfaceInitializedCallback)

        self.processed_logs = set()

        return True

    def onFinishedRunCallback(self, path : str, exit_code : int):
        new_logs = self.finder.get_crash_logs().difference(self.processed_logs)
        if not new_logs:
            return

        if not self.organizer.pluginSetting(self.name(), "offline_mode"):
            self.processor.update_database()

        for log in new_logs:
            self.processor.process_log(log)

        self.processed_logs.update(new_logs)

    def onUserInterfaceInitializedCallback(self, main_window : "QMainWindow"):
        game = self.organizer.managedGame().gameName()
        self.finder = crashlogs.get_finder(game)
        self.processor = CrashLogProcessor(game, lambda file : QFile(file).moveToTrash())

        if not self.organizer.pluginSetting(self.name(), "offline_mode"):
            self.processor.update_database()

        logs = self.finder.get_crash_logs()
        for log in logs:
            self.processor.process_log(log)
        self.processed_logs.update(logs)
