import json
import os
import sys
from typing import List, Optional, Union

import pydicom
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QLineEdit, QCheckBox, QMessageBox)
from pydicom.dataset import Dataset, FileDataset


class PlaceholderLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.placeholder_color = QColor('grey')
        self.default_color = self.palette().color(self.palette().ColorRole.Text)
        self.setPlaceholderText(placeholder)

    def get_actual_text(self) -> str:
        return self.text()

class DicomViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.last_file_path: Optional[str] = None
        self.config_file: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.search_results: List[QTreeWidgetItem] = []
        self.current_result_index: int = -1
        
        self.setWindowTitle('DICOM Viewer')
        self.create_widgets()
        self.load_last_file()

    def create_widgets(self) -> None:
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 创建顶部工具栏
        top_frame = QWidget()
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 添加按钮和控件
        self.open_button = QPushButton('打开DICOM文件', self)  # 添加父窗口
        self.open_button.clicked.connect(lambda: self.open_file())  # 修改信号槽连接
        top_layout.addWidget(self.open_button)

        # 搜索框和选项
        self.search_entry = PlaceholderLineEdit(
            placeholder="input anything and press F2/F3 for previous/next hit"
        )
        self.search_entry.textChanged.connect(self.search_tree)
        
        self.search_tag_check = QCheckBox('by Tag')
        self.search_name_check = QCheckBox('by Name')
        self.search_value_check = QCheckBox('by Value')
        
        self.search_tag_check.setChecked(True)
        self.search_name_check.setChecked(True)
        self.search_value_check.setChecked(True)

        self.prev_button = QPushButton('Previous')
        self.next_button = QPushButton('Next')
        
        self.prev_button.clicked.connect(self.goto_previous_result)
        self.next_button.clicked.connect(self.goto_next_result)

        # 添加搜索相关控件到布局
        top_layout.addStretch()
        top_layout.addWidget(self.search_entry)
        top_layout.addWidget(self.search_tag_check)
        top_layout.addWidget(self.search_name_check)
        top_layout.addWidget(self.search_value_check)
        top_layout.addWidget(self.prev_button)
        top_layout.addWidget(self.next_button)

        main_layout.addWidget(top_frame)

        # 创建树形视图
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tag", "Name", "VR", "Value"])
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 300)
        main_layout.addWidget(self.tree)

        # 创建状态栏
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)

        # 设置快捷键
        self.prev_button.setShortcut("F2")
        self.next_button.setShortcut("F3")

    def open_file(self, file_path: Optional[str] = None) -> None:
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                parent=self,  # 明确指定父窗口
                caption="打开DICOM文件",
                directory=os.path.dirname(self.last_file_path) if self.last_file_path else "",  # 添加默认目录
                filter="DICOM files (*.dcm);;All files (*.*)"
            )

        if file_path:
            try:
                self.tree.clear()
                ds: FileDataset = pydicom.dcmread(file_path)
                self.add_dicom_elements_to_tree(ds, None)
                self.setWindowTitle(f'DICOM Viewer - {os.path.basename(file_path)}')
                self.last_file_path = file_path
                self.update_status(f"已成功打开文件: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开DICOM文件: {e}")
                self.update_status(f"打开文件失败: {e}")

    def add_dicom_elements_to_tree(self, dataset: Union[Dataset, FileDataset], parent: Optional[QTreeWidgetItem]) -> None:
        for elem in dataset:
            tag_str = f"({elem.tag.group:04X},{elem.tag.element:04X})" if hasattr(elem, 'tag') else "Unknown"
            
            if parent is None:
                item = QTreeWidgetItem(self.tree)
            else:
                item = QTreeWidgetItem(parent)

            item.setText(0, tag_str)
            
            if elem.VR == "SQ":
                item.setText(1, elem.name)
                item.setText(2, "SQ")
                item.setText(3, f"序列: {len(elem.value)} 项")
                for i, seq_item in enumerate(elem.value):
                    child = QTreeWidgetItem(item)
                    child.setText(0, f"Item {i+1}")
                    self.add_dicom_elements_to_tree(seq_item, child)
            elif elem.name != 'Pixel Data':
                try:
                    value = str(elem.value) if hasattr(elem, 'value') else "N/A"
                    vr = elem.VR if hasattr(elem, 'VR') else "N/A"
                    item.setText(1, elem.name)
                    item.setText(2, vr)
                    item.setText(3, value)
                except Exception as e:
                    item.setText(1, elem.name)
                    item.setText(2, "N/A")
                    item.setText(3, f"无法显示: {e}")
            else:
                item.setText(1, elem.name)
                item.setText(2, elem.VR if hasattr(elem, 'VR') else "N/A")
                item.setText(3, "[图像数据]")

    def save_config(self) -> None:
        """保存最后打开的文件路径到配置文件"""
        try:
            config = {'last_file_path': self.last_file_path} if self.last_file_path else {}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            self.update_status(f"保存配置失败: {e}")

    def load_last_file(self) -> None:
        """从配置文件加载上次打开的文件路径并打开文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    last_file_path = config.get('last_file_path')
                    if last_file_path and os.path.exists(last_file_path):
                        self.open_file(last_file_path)
        except Exception as e:
            self.update_status(f"加载配置失败: {e}")

    def reset_search_results(self) -> None:
        """重置搜索结果"""
        self.search_results = []
        self.current_result_index = -1
        
        # 清除所有高亮
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            current_item = iterator.value()
            for col in range(current_item.columnCount()):
                current_item.setBackground(col, QColor('white'))
            iterator += 1

    def update_status(self, message: str) -> None:
        self.status_label.setText(message)

    def search_tree(self) -> None:
        search_text = self.search_entry.get_actual_text().strip().lower()
        if not search_text:
            self.update_status("请输入搜索内容")
            return

        self.reset_search_results()

        search_tag = self.search_tag_check.isChecked()
        search_name = self.search_name_check.isChecked()
        search_value = self.search_value_check.isChecked()

        if not any([search_tag, search_name, search_value]):
            self.update_status("请至少选择一个搜索选项")
            return

        self.search_results = self.find_matching_items(search_text, search_tag, search_name, search_value)

        if self.search_results:
            self.update_status(f"找到 {len(self.search_results)} 个匹配项")
            self.goto_next_result()
        else:
            self.update_status(f"未找到匹配项: {search_text}")

    def find_matching_items(self, search_text: str, search_tag: bool, search_name: bool, search_value: bool) -> List[QTreeWidgetItem]:
        results = []
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if (search_tag and search_text in item.text(0).lower()) or \
               (search_name and search_text in item.text(1).lower()) or \
               (search_value and search_text in item.text(3).lower()):
                results.append(item)
            iterator += 1
        return results

    def highlight_current_result(self) -> None:
        if not self.search_results or self.current_result_index < 0 or \
           self.current_result_index >= len(self.search_results):
            return

        item = self.search_results[self.current_result_index]
        
        # 重置所有项的背景色
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            current_item = iterator.value()
            for col in range(current_item.columnCount()):
                current_item.setBackground(col, QColor('white'))
            iterator += 1

        # 高亮当前项
        for col in range(item.columnCount()):
            item.setBackground(col, QColor('yellow'))
        
        # 确保项目可见
        self.tree.scrollToItem(item)
        self.update_status(f"结果 {self.current_result_index + 1}/{len(self.search_results)}")

    def goto_next_result(self) -> None:
        if not self.search_results:
            return
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        self.highlight_current_result()

    def goto_previous_result(self) -> None:
        if not self.search_results:
            return
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
        self.highlight_current_result()

    def closeEvent(self, event):
        self.save_config()
        self.update_status("正在关闭程序...")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = DicomViewer()
    viewer.showMaximized()
    sys.exit(app.exec())
