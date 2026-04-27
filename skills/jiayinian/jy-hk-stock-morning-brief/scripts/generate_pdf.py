#!/usr/bin/env python3
"""
港股资讯早报 PDF 生成脚本
将 Markdown 报告转换为 PDF 格式

依赖：
- markdown2pdf 或 weasyprint
- 或使用 openclaw 的 pdf 技能

Usage:
    python generate_pdf.py --input hk-brief-20260326.md --output hk-brief-20260326.pdf
"""

import argparse
import os
import sys


def check_dependencies():
    """
    检查 PDF 生成依赖
    """
    deps = []
    
    # 尝试导入 markdown2pdf
    try:
        import markdown2pdf
        deps.append("markdown2pdf")
    except ImportError:
        pass
    
    # 尝试导入 weasyprint
    try:
        import weasyprint
        deps.append("weasyprint")
    except ImportError:
        pass
    
    return deps


def generate_pdf_markdown2pdf(input_path: str, output_path: str):
    """
    使用 markdown2pdf 生成 PDF
    """
    from markdown2pdf import convert
    
    with open(input_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    convert(markdown_content, output_path)
    print(f"[INFO] PDF 已生成：{output_path}")


def generate_pdf_weasyprint(input_path: str, output_path: str):
    """
    使用 weasyprint 生成 PDF
    """
    from weasyprint import HTML
    
    # 读取 Markdown 并转换为 HTML（需要 markdown 库）
    import markdown
    
    with open(input_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    html_content = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'toc']
    )
    
    # 添加基础 HTML 包装和 CSS 样式
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: "SimSun", "宋体", serif;
                line-height: 1.6;
                margin: 2cm;
                font-size: 11pt;
            }}
            h1, h2, h3 {{
                color: #333;
                border-bottom: 2px solid #ef232a;
                padding-bottom: 0.3em;
            }}
            h1 {{ font-size: 18pt; }}
            h2 {{ font-size: 14pt; }}
            h3 {{ font-size: 12pt; }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 0.5em;
                text-align: center;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
            }}
            .disclaimer {{
                font-size: 9pt;
                color: #666;
                border-top: 1px solid #ddd;
                padding-top: 1em;
                margin-top: 2em;
            }}
            @page {{
                size: A4;
                margin: 2cm;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    HTML(string=full_html).write_pdf(output_path)
    print(f"[INFO] PDF 已生成：{output_path}")


def main():
    parser = argparse.ArgumentParser(description="港股资讯早报 PDF 生成")
    parser.add_argument("--input", type=str, required=True, help="输入 Markdown 文件路径")
    parser.add_argument("--output", type=str, required=True, help="输出 PDF 文件路径")
    parser.add_argument(
        "--engine",
        type=str,
        choices=["auto", "markdown2pdf", "weasyprint"],
        default="auto",
        help="PDF 生成引擎"
    )
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"[ERROR] 输入文件不存在：{args.input}")
        sys.exit(1)
    
    # 检查依赖
    available_deps = check_dependencies()
    print(f"[INFO] 可用的 PDF 引擎：{available_deps if available_deps else '无'}")
    
    # 选择引擎
    if args.engine == "auto":
        if "weasyprint" in available_deps:
            engine = "weasyprint"
        elif "markdown2pdf" in available_deps:
            engine = "markdown2pdf"
        else:
            print("[ERROR] 未找到可用的 PDF 生成引擎")
            print("[INFO] 请安装：pip install weasyprint 或 pip install markdown2pdf")
            print("[INFO] 或使用 openclaw 的 pdf 技能进行转换")
            sys.exit(1)
    else:
        engine = args.engine
        if engine not in available_deps:
            print(f"[ERROR] 指定的引擎 {engine} 不可用")
            sys.exit(1)
    
    print(f"[INFO] 使用引擎：{engine}")
    
    # 生成 PDF
    try:
        if engine == "weasyprint":
            generate_pdf_weasyprint(args.input, args.output)
        elif engine == "markdown2pdf":
            generate_pdf_markdown2pdf(args.input, args.output)
        
        print(f"[SUCCESS] PDF 生成完成：{args.output}")
        
    except Exception as e:
        print(f"[ERROR] PDF 生成失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
