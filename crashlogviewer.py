import os
from typing import *
from mobase import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class CrashLogViewer(IPluginTool):

    def __init__(self):
        super().__init__()

    def name(self) -> str:
        return "Crash Log Viewer"

    def version(self) -> "VersionInfo":
        return VersionInfo(0, 0, 0, 0, ReleaseType.ALPHA)

    def description(self) -> str:
        return "Lists crash logs"

    def author(self) -> str:
        return "Parapets"

    def requirements(self) -> List["IPluginRequirement"]:
        return [
            PluginRequirementFactory.gameDependency({
                "Skyrim Special Edition",
            })
        ]

    def settings(self) -> List["PluginSetting"]:
        return []

    def displayName(self) -> str:
        return "Crash Log Viewer"

    def tooltip(self) -> str:
        return "View crash logs"

    def icon(self) -> "QIcon":
        return QIcon()

    def init(self, organizer : "IOrganizer") -> bool:
        self.organizer = organizer
        organizer.onUserInterfaceInitialized(self.onUserInterfaceInitializedCallback)
        return True

    def display(self) -> None:
        self.dialog.show()

    def onUserInterfaceInitializedCallback(self, main_window : "QMainWindow"):
        self.dialog = self.make_dialog()

    def make_dialog(self) -> "QDialog":
        documents = self.organizer.managedGame().documentsDirectory()
        log_dir = os.path.join(documents.absolutePath(), "SKSE")

        source_model = QFileSystemModel()
        source_model.setRootPath(log_dir)

        proxy_model = FileFilterProxyModel()
        proxy_model.setSourceModel(source_model)
        proxy_model.setFilterWildcard("crash-*.log")

        dialog = QDialog()
        dialog.setWindowTitle("Crash Log Viewer")

        list = FileView(dialog)
        list.setModel(proxy_model)
        list.setRootIndex(proxy_model.mapFromSource(source_model.index(log_dir)))
        list.setMinimumWidth(list.sizeHintForColumn(0))
        list.setDragEnabled(True)

        button_box = QDialogButtonBox(dialog)
        button_box.setOrientation(Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Close)
        #button_box.rejected.connect(dialog.reject)

        layout = QVBoxLayout()
        layout.addWidget(list)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        return dialog

class FileView(QListView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def edit(
        self,
        index : "QModelIndex",
        trigger : "EditTrigger",
        event : "QEvent"
    ) -> bool:
        if trigger in (QAbstractItemView.DoubleClicked, QAbstractItemView.EditKeyPressed):
            os.startfile(self.model().filePath(index))
        return False

class FileFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filePath(self, index : "QModelIndex") -> str:
        return self.sourceModel().filePath(self.mapToSource(index))

    def filterAcceptsRow(self, source_row : int, source_parent : "QModelIndex") -> bool:
        source_model = self.sourceModel()
        if source_parent == source_model.index(source_model.rootPath()):
            return super().filterAcceptsRow(source_row, source_parent)
        return True
