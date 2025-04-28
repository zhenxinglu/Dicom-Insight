# DicomInsight

这是一个基于PyQt 6的查看和修改DICOM文件的GUI工具。其功能如下：

1. Python代码要采用type hint。
2. 通过"Open"按钮或者拖拽方式打开DICOM文件。
3. 用结构化树状形式显示DICOM文件的内容，直接显示DICOM元素而不显示最顶层的文件节点。
4. 支持按tag的名字, 值或者tag的描述内容来搜索tag。
5. 支持实时搜索功能，在搜索框输入关键字时会即时显示搜索结果，无需按回车键触发。
6. 支持键盘快捷键：F3键跳转到下一个搜索结果，F2键跳转到上一个搜索结果。
7. 支持DICOM文件的修改并保存。

---

This is a GUI tool based on PyQt 6 for viewing and modifying DICOM files. Its features are as follows:

1. Python code uses type hints.
2. Open DICOM files via the "Open" button or drag-and-drop functionality.
3. Display DICOM file contents in a structured tree view, showing DICOM elements directly without displaying the top-level file node.
4. Support searching tags by tag name, value, or tag description content.
5. Support real-time search functionality, displaying search results instantly as keywords are typed, without needing to press Enter.
6. Support keyboard shortcuts: F3 key to jump to next search result, F2 key to jump to previous search result.
7. Support DICOM file modification and saving.
