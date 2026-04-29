#!/usr/bin/env python3
"""
SQL 拆分工具 - GUI 界面
提供图形化界面进行 SQL 文件拆分操作
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
from pathlib import Path
from typing import Optional, List
import json
import os

# 导入核心模块
from split_sql_v21 import split_sql_file, SQLDialect
from error_handler import SplitResult, SplitError


class SQLSplitterGUI:
    """SQL 拆分工具 GUI"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SQL 拆分工具 v2.2")
        self.root.geometry("900x700")

        # 配置
        self.config_file = Path.home() / ".sql_splitter_config.json"
        self.config = self.load_config()

        # 任务队列和线程
        self.task_queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False

        # 创建界面
        self.create_widgets()
        self.load_config_to_ui()

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # === 输入文件选择 ===
        ttk.Label(main_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_file_var = tk.StringVar()
        input_entry = ttk.Entry(main_frame, textvariable=self.input_file_var, width=60)
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_input_file).grid(row=0, column=2, padx=5, pady=5)

        # === 输出目录选择 ===
        ttk.Label(main_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar()
        output_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, width=60)
        output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_output_dir).grid(row=1, column=2, padx=5, pady=5)

        # === 方言选择 ===
        ttk.Label(main_frame, text="SQL 方言:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.dialect_var = tk.StringVar(value="auto")
        dialect_frame = ttk.Frame(main_frame)
        dialect_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        dialects = ["auto", "mysql", "postgresql", "oracle", "sqlserver", "dm", "generic"]
        for i, dialect in enumerate(dialects):
            ttk.Radiobutton(dialect_frame, text=dialect.upper(), variable=self.dialect_var,
                           value=dialect).grid(row=0, column=i, padx=5)

        # === 选项 ===
        options_frame = ttk.LabelFrame(main_frame, text="选项", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.dry_run_var = tk.BooleanVar(value=False)
        self.no_merge_var = tk.BooleanVar(value=False)
        self.show_progress_var = tk.BooleanVar(value=True)
        self.verbose_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="预览模式 (不实际创建文件)",
                       variable=self.dry_run_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="不生成合并脚本",
                       variable=self.no_merge_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="显示进度条",
                       variable=self.show_progress_var).grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="详细输出",
                       variable=self.verbose_var).grid(row=1, column=1, sticky=tk.W, padx=5)

        # === 操作按钮 ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="开始拆分", command=self.start_split,
                  width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="停止", command=self.stop_split,
                  width=15).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="清空输出", command=self.clear_output,
                  width=15).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="保存配置", command=self.save_config_from_ui,
                  width=15).grid(row=0, column=3, padx=5)

        # === 进度条 ===
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(progress_frame, text="进度:").grid(row=0, column=0, sticky=tk.W)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, length=600)
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=2, padx=5)

        progress_frame.columnconfigure(1, weight=1)

        # === 输出区域 ===
        output_frame = ttk.LabelFrame(main_frame, text="输出", padding="10")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80,
                                                    wrap=tk.WORD, state='disabled')
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        main_frame.rowconfigure(6, weight=1)

    def browse_input_file(self):
        """浏览输入文件"""
        filename = filedialog.askopenfilename(
            title="选择 SQL 文件",
            filetypes=[("SQL 文件", "*.sql"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
            # 自动设置输出目录
            input_path = Path(filename)
            default_output = input_path.parent / f"{input_path.stem}_split"
            self.output_dir_var.set(str(default_output))

    def browse_output_dir(self):
        """浏览输出目录"""
        dirname = filedialog.askdirectory(title="选择输出目录")
        if dirname:
            self.output_dir_var.set(dirname)

    def load_config(self) -> dict:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log_message(f"加载配置失败: {e}", "error")
        return {}

    def save_config(self, config: dict):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_message(f"保存配置失败: {e}", "error")

    def load_config_to_ui(self):
        """从配置加载到UI"""
        if 'last_input_file' in self.config:
            self.input_file_var.set(self.config['last_input_file'])
        if 'last_output_dir' in self.config:
            self.output_dir_var.set(self.config['last_output_dir'])
        if 'dialect' in self.config:
            self.dialect_var.set(self.config['dialect'])
        if 'dry_run' in self.config:
            self.dry_run_var.set(self.config['dry_run'])
        if 'no_merge' in self.config:
            self.no_merge_var.set(self.config['no_merge'])
        if 'show_progress' in self.config:
            self.show_progress_var.set(self.config['show_progress'])
        if 'verbose' in self.config:
            self.verbose_var.set(self.config['verbose'])

    def save_config_from_ui(self):
        """从UI保存配置"""
        config = {
            'last_input_file': self.input_file_var.get(),
            'last_output_dir': self.output_dir_var.get(),
            'dialect': self.dialect_var.get(),
            'dry_run': self.dry_run_var.get(),
            'no_merge': self.no_merge_var.get(),
            'show_progress': self.show_progress_var.get(),
            'verbose': self.verbose_var.get()
        }
        self.save_config(config)
        messagebox.showinfo("成功", "配置已保存")

    def log_message(self, message: str, level: str = "info"):
        """记录消息到输出区域"""
        self.output_text.config(state='normal')

        # 添加时间戳
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 根据级别设置颜色标签
        tag = level
        if level == "error":
            self.output_text.tag_config("error", foreground="red")
        elif level == "warning":
            self.output_text.tag_config("warning", foreground="orange")
        elif level == "success":
            self.output_text.tag_config("success", foreground="green")
        else:
            self.output_text.tag_config("info", foreground="black")

        self.output_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')

    def clear_output(self):
        """清空输出"""
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state='disabled')
        self.progress_var.set(0)
        self.progress_label.config(text="0%")

    def update_progress(self, value: int, total: int):
        """更新进度条"""
        if total > 0:
            percentage = int((value / total) * 100)
            self.progress_var.set(percentage)
            self.progress_label.config(text=f"{percentage}%")

    def start_split(self):
        """开始拆分"""
        # 验证输入
        input_file = self.input_file_var.get()
        if not input_file:
            messagebox.showerror("错误", "请选择输入文件")
            return

        if not Path(input_file).exists():
            messagebox.showerror("错误", f"文件不存在: {input_file}")
            return

        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        # 禁用开始按钮
        self.is_running = True

        # 清空输出
        self.clear_output()

        # 启动工作线程
        self.worker_thread = threading.Thread(target=self.run_split_task, daemon=True)
        self.worker_thread.start()

    def stop_split(self):
        """停止拆分"""
        if self.is_running:
            self.is_running = False
            self.log_message("正在停止...", "warning")

    def run_split_task(self):
        """运行拆分任务（在工作线程中）"""
        try:
            input_file = self.input_file_var.get()
            output_dir = self.output_dir_var.get()
            dialect_str = self.dialect_var.get()

            # 转换方言
            dialect = None
            if dialect_str != "auto":
                dialect = SQLDialect[dialect_str.upper()]

            self.log_message(f"开始拆分: {input_file}", "info")
            self.log_message(f"输出目录: {output_dir}", "info")
            self.log_message(f"方言: {dialect_str.upper()}", "info")

            # 模拟进度更新
            self.update_progress(1, 100)

            # 调用拆分函数
            result = split_sql_file(
                input_file,
                output_dir,
                dialect=dialect,
                verbose=self.verbose_var.get(),
                dry_run=self.dry_run_var.get(),
                show_progress=self.show_progress_var.get(),
                no_merge=self.no_merge_var.get()
            )

            # 更新进度
            self.update_progress(100, 100)

            # 显示结果
            if result.success:
                self.log_message(f"拆分完成! 共 {result.total} 个文件", "success")
                self.log_message(f"输出目录: {result.output_dir}", "info")

                # 显示统计信息
                if result.stats:
                    self.log_message("统计信息:", "info")
                    for obj_type, count in sorted(result.stats.items()):
                        self.log_message(f"  {obj_type}: {count}", "info")

                # 显示警告
                if result.warnings:
                    self.log_message(f"警告: {len(result.warnings)} 个", "warning")
                    for warning in result.warnings:
                        self.log_message(f"  - {warning}", "warning")
            else:
                self.log_message("拆分失败!", "error")
                for error in result.errors:
                    self.log_message(f"  - {error}", "error")

            # 保存配置
            self.save_config_from_ui()

        except Exception as e:
            self.log_message(f"错误: {e}", "error")
            import traceback
            self.log_message(traceback.format_exc(), "error")
        finally:
            self.is_running = False


def main():
    """主函数"""
    root = tk.Tk()
    app = SQLSplitterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
