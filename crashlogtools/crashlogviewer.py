import os
from typing import *
from mobase import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from . import crashlogs

class CrashLogViewer(IPluginTool):
    def __init__(self):
        super().__init__()

    def name(self) -> str:
        return "Crash Log Viewer"

    def version(self) -> "VersionInfo":
        return VersionInfo(1, 0, 0, 0, ReleaseType.FINAL)

    def description(self) -> str:
        return "Lists crash logs"

    def author(self) -> str:
        return "Parapets"

    def requirements(self) -> List["IPluginRequirement"]:
        return [
            PluginRequirementFactory.gameDependency(crashlogs.supported_games())
        ]

    def settings(self) -> List["PluginSetting"]:
        return []

    def displayName(self) -> str:
        return "Crash Log Viewer"

    def tooltip(self) -> str:
        return "View crash logs"

    def icon(self) -> "QIcon":
        return QIcon()

    def init(self, organizer: "IOrganizer") -> bool:
        self.organizer = organizer
        organizer.onUserInterfaceInitialized(self.onUserInterfaceInitializedCallback)
        return True

    def display(self) -> None:
        self.dialog.show()

    def onUserInterfaceInitializedCallback(self, main_window: "QMainWindow"):
        game = self.organizer.managedGame().gameName()
        self.finder = crashlogs.get_finder(game)
        self.dialog = self.make_dialog(main_window)

    def make_dialog(self, main_window: "QMainWindow") -> "QDialog":
        log_dir = self.finder.log_directory

        source_model = QFileSystemModel()
        source_model.setRootPath(log_dir)

        proxy_model = FileFilterProxyModel()
        proxy_model.setSourceModel(source_model)
        proxy_model.setFilterWildcard(self.finder.filter)
        proxy_model.sort(0, Qt.SortOrder.DescendingOrder)

        dialog = QDialog(main_window)
        dialog.setWindowTitle("Crash Log Viewer")

        list_view = QListView(dialog)
        list_view.setModel(proxy_model)
        list_view.setRootIndex(proxy_model.mapFromSource(source_model.index(log_dir)))
        list_view.setDragEnabled(True)
        list_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        def open(index: "QModelIndex") -> None:
            source_index = proxy_model.mapToSource(index)
            os.startfile(source_model.filePath(source_index))

        def delete(index: "QModelIndex") -> None:
            source_index = proxy_model.mapToSource(index)
            file_path = source_model.filePath(source_index)
            print(f"Attempting to delete file: {file_path}")  # Debug statement
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} deleted successfully.")  # Debug statement
            else:
                print(f"File {file_path} not found.")  # Debug statement

        def for_selected(action: Callable[["QModelIndex"], None]) -> Callable[[bool], None]:
            def fn(checked: bool):
                for index in list_view.selectedIndexes():
                    action(index)
            return fn

        open_action = QAction(list_view.tr("&Open"), list_view)
        open_action.triggered.connect(for_selected(open))
        f = open_action.font()
        f.setBold(True)
        open_action.setFont(f)
        list_view.addAction(open_action)

        delete_action = QAction(list_view.tr("&Delete"), list_view)
        delete_action.triggered.connect(for_selected(delete))
        list_view.addAction(delete_action)

        list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        list_view.activated.connect(open)

        button_box = QDialogButtonBox(dialog)
        button_box.setOrientation(Qt.Orientation.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        button_box.button(QDialogButtonBox.StandardButton.Close).setAutoDefault(False)

        layout = QVBoxLayout()
        layout.addWidget(list_view)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        return dialog

class FileFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filePath(self, index: "QModelIndex") -> str:
        return self.sourceModel().filePath(self.mapToSource(index))

    def filterAcceptsRow(self, source_row: int, source_parent: "QModelIndex") -> bool:
        source_model = self.sourceModel()
        if source_parent == source_model.index(source_model.rootPath()):
            return super().filterAcceptsRow(source_row, source_parent)
        return True
