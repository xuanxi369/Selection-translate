from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QCheckBox, QWidget, QHBoxLayout
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtCore import QThread, pyqtSignal, QEvent, Qt
from pynput.mouse import Listener, Button
from easygoogletranslate import EasyGoogleTranslate
import sys, re
import pyperclip
import pyautogui

# 初始化翻译器
translator = EasyGoogleTranslate(
    source_language='auto',  # 自动检测语言
    target_language='zh-CN',  # 目标语言设置为中文
    timeout=10  # 超时时间设置为10秒
)

# 自定义线程类，用于监听鼠标点击事件
class UpdateThread(QThread):
    # 定义一个信号，用于通知主线程更新文本
    update_text_signal = pyqtSignal(str)

    def run(self):
        """线程的主要执行逻辑，监听鼠标左键点击事件"""
        def on_click(x, y, button, pressed):
            # 检测到左键释放事件时，发送信号
            if button == Button.left and not pressed:
                self.update_text_signal.emit('not pressed')

        # 使用pynput监听鼠标事件
        with Listener(on_click=on_click) as listener:
            listener.join()

# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self, clipboard, parent=None):
        super(MainWindow, self).__init__(parent)
        self.clipboard = clipboard  # 保存系统的剪贴板对象
        self.previous_clipboard_text = ""  # 保存上一次的剪贴板内容

        # 设置窗口大小和标题
        self.setGeometry(100, 500, 500, 700)
        self.setWindowTitle('☀')  # 设置窗口标题
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 窗口始终置顶

        # 创建文本框
        self.textbox = QTextEdit(self)
        self.setCentralWidget(self.textbox)
        self.textbox.setStyleSheet("background-color: black; color: white;")  # 设置文本框的样式

        # 创建布局容器和复选框
        container = QWidget(self)
        layout = QHBoxLayout(container)

        # 创建复选框1 - 控制翻译功能开关
        self.translation_enabled_checkbox = QCheckBox("Open", self)
        self.translation_enabled_checkbox.setShortcut(QKeySequence("Alt+t"))
        layout.addWidget(self.translation_enabled_checkbox)

        # 创建复选框2 - 模拟剪贴板复制操作
        self.simulate_copy_checkbox = QCheckBox("Mark", self)
        self.simulate_copy_checkbox.setChecked(True)
        self.simulate_copy_checkbox.setShortcut(QKeySequence("Alt+y"))
        layout.addWidget(self.simulate_copy_checkbox)

        # 创建复选框3 - 控制是否显示原文
        self.show_original_checkbox = QCheckBox("With original text", self)
        self.show_original_checkbox.setShortcut(QKeySequence("Alt+u"))
        layout.addWidget(self.show_original_checkbox)

        # 设置菜单部件
        self.setMenuWidget(container)

        # 设置文本框的字体
        font = self.textbox.font()
        font.setPointSize(26)
        self.textbox.setFont(font)

        # 启动鼠标监听线程
        self.start_thread()

        # 设置事件过滤器，处理拖动窗口等事件
        self.textbox.installEventFilter(self)
        self.drag_pos = None  # 用于保存拖动时的初始位置

    def check_clipboard(self):
        """检查剪贴板内容并进行翻译"""
        if not self.translation_enabled_checkbox.isChecked():
            return  # 如果翻译功能未开启，则直接返回

        if self.simulate_copy_checkbox.isChecked():
            # 如果勾选模拟复制操作，则发送Ctrl+C指令复制文本
            pyautogui.hotkey("ctrl", "c")

        # 获取剪贴板的当前文本
        clipboard_text = self.clipboard.text()

        # 限制文本长度，避免过长文本影响性能
        if isinstance(clipboard_text, str) and len(clipboard_text) < 3000:
            clipboard_text = re.sub(r'\s+', ' ', clipboard_text.strip())  # 清理多余的空白字符

            # 如果当前剪贴板内容与之前不同，则进行翻译
            if clipboard_text != self.previous_clipboard_text:
                self.previous_clipboard_text = clipboard_text  # 更新保存的剪贴板文本
                try:
                    # 执行翻译
                    translation = translator.translate(clipboard_text)
                    if self.show_original_checkbox.isChecked():
                        # 如果勾选显示原文，则显示翻译和原文
                        self.textbox.setText(f"{translation}\n{clipboard_text}")
                    else:
                        # 只显示翻译结果
                        self.textbox.setText(translation)
                except Exception as e:
                    print(f"翻译失败: {e}")  # 打印异常信息以便调试

    def start_thread(self):
        """启动鼠标监听线程"""
        self.listener_thread = UpdateThread(self)  # 创建监听线程实例
        self.listener_thread.update_text_signal.connect(self.check_clipboard)  # 连接信号与槽
        self.listener_thread.start()  # 启动线程

    def eventFilter(self, obj, event):
        """事件过滤器，用于处理窗口的拖动和字体调整"""
        if obj is self.textbox:
            if event.type() == QEvent.MouseButtonPress and event.buttons() == Qt.LeftButton:
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()  # 保存初始拖动位置
            elif event.type() == QEvent.MouseMove and self.drag_pos:
                self.move(event.globalPos() - self.drag_pos)  # 移动窗口
            elif event.type() == QEvent.Wheel and event.modifiers() == Qt.ControlModifier:
                # 通过Ctrl+滚轮调整字体大小
                font = self.textbox.font()
                delta = event.angleDelta().y() / 120  # 每次滚动单位为120
                new_size = font.pointSize() + delta
                if new_size > 0:
                    font.setPointSize(int(new_size))  # 设置新的字体大小
                    self.textbox.setFont(font)
            return True
        return super().eventFilter(obj, event)  # 调用父类的事件过滤器

# 程序入口
if __name__ == '__main__':
    app = QApplication(sys.argv)
    clipboard = app.clipboard()  # 获取系统剪贴板对象
    window = MainWindow(clipboard)  # 创建主窗口实例
    window.show()  # 显示窗口
    sys.exit(app.exec_())  # 进入应用主循环
