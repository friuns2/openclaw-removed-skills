#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
word-to-pdf.py — Word → PDF 转换器 v2.0

修复：
  - 旧版 main 里的 argparse 写错（`elif arg in sys.argv[...:` 缺右括号），整体重写
  - 跨平台后端：macOS / Linux / Windows
  - 后端策略：① LibreOffice/WPS 命令行（首选）② docx2pdf (Windows / macOS Office) ③ MS Word COM (Windows)
  - 输出后自动校验 PDF 有效（>1KB 且包含 %PDF）
  - --keep-fonts：转换时保留嵌入字体（避免对方机器替换字体）
  - --quiet / --verbose
"""

import os
import sys
import glob
import shutil
import subprocess
import argparse
import platform


# ============================================================
# 一、后端检测
# ============================================================

LIBREOFFICE_PATHS = [
    # macOS
    '/Applications/LibreOffice.app/Contents/MacOS/soffice',
    '/Applications/wpsoffice.app/Contents/MacOS/wpsoffice',
    '/Applications/WPSOffice.app/Contents/MacOS/wpsoffice',
    '/opt/homebrew/bin/soffice',
    '/usr/local/bin/soffice',
    # Linux
    '/usr/bin/soffice',
    '/usr/bin/libreoffice',
    '/snap/bin/libreoffice',
    # Windows
    r'C:\Program Files\LibreOffice\program\soffice.exe',
    r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
    r'C:\Program Files\Kingsoft\WPS Office\office6\wps.exe',
    # PATH lookups
    'soffice',
    'libreoffice',
]


def find_libreoffice():
    """按 LIBREOFFICE_PATHS 顺序找第一个可用的 soffice。"""
    for path in LIBREOFFICE_PATHS:
        if os.sep in path or '/' in path:
            if os.path.exists(path):
                return path
        else:
            located = shutil.which(path)
            if located:
                return located
    return None


def find_docx2pdf():
    """docx2pdf 仅在 macOS / Windows 且装了 Microsoft Office 时可用。"""
    try:
        import docx2pdf  # noqa: F401
        return True
    except ImportError:
        return False


def find_word_com():
    if platform.system() != 'Windows':
        return False
    try:
        import win32com.client  # noqa: F401
        return True
    except ImportError:
        return False


def detect_backends():
    backends = []
    lo = find_libreoffice()
    if lo:
        backends.append(('libreoffice', lo))
    if find_docx2pdf():
        backends.append(('docx2pdf', None))
    if find_word_com():
        backends.append(('word_com', None))
    return backends


# ============================================================
# 二、转换实现
# ============================================================

def _validate_pdf(path):
    if not os.path.exists(path):
        return False, 'PDF 不存在'
    if os.path.getsize(path) < 1024:
        return False, 'PDF 文件过小（<1KB），可能转换失败'
    try:
        with open(path, 'rb') as f:
            head = f.read(8)
        if not head.startswith(b'%PDF-'):
            return False, 'PDF 文件头无效'
    except OSError as e:
        return False, f'读取失败: {e}'
    return True, ''


def convert_with_libreoffice(input_path, output_path, lo_path, timeout=120,
                             keep_fonts=True):
    """LibreOffice / WPS 命令行转换。可选嵌入字体。"""
    temp_dir = os.path.join(os.path.dirname(output_path) or '.',
                            '.pdf_convert_tmp')
    os.makedirs(temp_dir, exist_ok=True)

    try:
        temp_input = os.path.join(temp_dir, os.path.basename(input_path))
        shutil.copy2(input_path, temp_input)

        if keep_fonts:
            convert_filter = 'pdf:writer_pdf_Export:EmbedStandardFonts=true'
        else:
            convert_filter = 'pdf'

        cmd = [
            lo_path,
            '--headless',
            '--norestore', '--nolockcheck', '--nodefault',
            '--convert-to', convert_filter,
            '--outdir', temp_dir,
            os.path.basename(temp_input),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=temp_dir,
        )
        if result.returncode != 0:
            return False, f'LibreOffice 失败: {result.stderr.strip() or result.stdout.strip()}'

        temp_pdf = os.path.splitext(os.path.basename(temp_input))[0] + '.pdf'
        temp_pdf_path = os.path.join(temp_dir, temp_pdf)
        if not os.path.exists(temp_pdf_path):
            return False, 'LibreOffice 转换后未找到 PDF 输出'

        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        shutil.move(temp_pdf_path, output_path)
        return True, output_path
    except subprocess.TimeoutExpired:
        return False, 'LibreOffice 超时'
    except Exception as e:  # pragma: no cover
        return False, f'LibreOffice 异常: {e}'
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def convert_with_docx2pdf(input_path, output_path):
    try:
        from docx2pdf import convert
        convert(input_path, output_path)
        return True, output_path
    except Exception as e:
        return False, f'docx2pdf 失败: {e}'


def convert_with_word_com(input_path, output_path):
    try:
        import win32com.client  # noqa
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        try:
            doc = word.Documents.Open(os.path.abspath(input_path))
            doc.SaveAs(os.path.abspath(output_path), FileFormat=17)
            doc.Close()
        finally:
            word.Quit()
        return True, output_path
    except Exception as e:
        return False, f'Word COM 失败: {e}'


# ============================================================
# 三、对外 API
# ============================================================

def convert_to_pdf(input_path, output_path=None, timeout=120,
                   backend='auto', keep_fonts=True, verbose=False):
    """转换 Word → PDF。

    backend ∈ {'auto', 'libreoffice', 'docx2pdf', 'word_com'}
    """
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        return False, f'文件不存在: {input_path}'
    if not input_path.lower().endswith(('.docx', '.doc')):
        return False, '仅支持 .docx / .doc'

    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.pdf'
    else:
        output_path = os.path.abspath(output_path)

    backends = detect_backends()
    if backend != 'auto':
        backends = [b for b in backends if b[0] == backend]
        if not backends:
            return False, f'指定后端不可用: {backend}'

    if not backends:
        return False, ('没有可用 PDF 转换后端。请安装：\n'
                       '  brew install --cask libreoffice  # macOS\n'
                       '  apt install libreoffice          # Linux\n'
                       '  pip install docx2pdf             # 已装 Office')

    last_err = ''
    for name, path in backends:
        if verbose:
            print(f'→ 尝试后端: {name}', file=sys.stderr)
        if name == 'libreoffice':
            ok, msg = convert_with_libreoffice(
                input_path, output_path, path,
                timeout=timeout, keep_fonts=keep_fonts,
            )
        elif name == 'docx2pdf':
            ok, msg = convert_with_docx2pdf(input_path, output_path)
        elif name == 'word_com':
            ok, msg = convert_with_word_com(input_path, output_path)
        else:
            ok, msg = False, f'未知后端 {name}'
        if ok:
            valid, err = _validate_pdf(output_path)
            if valid:
                return True, output_path
            last_err = f'{name} 输出无效: {err}'
            continue
        last_err = msg

    return False, f'全部后端失败。最后错误: {last_err}'


def convert_batch(input_paths, output_dir=None, **kwargs):
    expanded = []
    for path in input_paths:
        if any(c in path for c in '*?['):
            expanded.extend(glob.glob(path))
        else:
            expanded.append(path)

    results = {'success': [], 'failed': []}
    for input_path in expanded:
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.basename(input_path)
            output_path = os.path.join(
                output_dir, os.path.splitext(filename)[0] + '.pdf')
        else:
            output_path = None
        ok, result = convert_to_pdf(input_path, output_path, **kwargs)
        if ok:
            results['success'].append(result)
        else:
            results['failed'].append({'file': input_path, 'error': result})
    return results


# ============================================================
# 四、CLI
# ============================================================

def _build_parser():
    parser = argparse.ArgumentParser(
        prog='word-to-pdf',
        description='Word → PDF 转换器 v2.0（多后端 + 跨平台）',
    )
    parser.add_argument('inputs', nargs='*',
                        help='输入 .docx / .doc 文件，可多个或通配符')
    parser.add_argument('--output', '-o', default=None,
                        help='单文件模式下的输出 PDF 路径')
    parser.add_argument('--output-dir', '-d', default=None,
                        help='批量模式下的输出目录')
    parser.add_argument('--backend', default='auto',
                        choices=['auto', 'libreoffice', 'docx2pdf',
                                 'word_com'])
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--no-embed-fonts', action='store_true',
                        help='不嵌入字体（默认嵌入，避免接收方字体替换）')
    parser.add_argument('--list-backends', action='store_true',
                        help='只显示可用后端然后退出')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)

    if args.list_backends:
        backends = detect_backends()
        if not backends:
            print('（无可用后端）')
            return 1
        for name, path in backends:
            print(f'{name}: {path or "OK"}')
        return 0

    if not args.inputs:
        _build_parser().print_help()
        backends = detect_backends()
        print('\n可用后端:', [n for n, _ in backends] or '（无）')
        return 1

    expanded = []
    for path in args.inputs:
        if any(c in path for c in '*?['):
            expanded.extend(glob.glob(path))
        else:
            expanded.append(path)

    if not expanded:
        print('错误: 没有匹配的文件', file=sys.stderr)
        return 1

    keep_fonts = not args.no_embed_fonts
    common_kwargs = dict(timeout=args.timeout, backend=args.backend,
                         keep_fonts=keep_fonts, verbose=args.verbose)

    if len(expanded) == 1 and args.output_dir is None:
        ok, result = convert_to_pdf(expanded[0], args.output,
                                    **common_kwargs)
        if ok:
            if not args.quiet:
                print(f'✅ {result}')
            return 0
        print(f'❌ {result}', file=sys.stderr)
        return 1

    results = convert_batch(expanded, args.output_dir, **common_kwargs)
    if not args.quiet:
        print(f'\n转换完成: 成功 {len(results["success"])} / '
              f'失败 {len(results["failed"])}')
        for r in results['success']:
            print(f'  ✅ {r}')
        for item in results['failed']:
            print(f'  ❌ {item["file"]}: {item["error"]}', file=sys.stderr)
    return 0 if not results['failed'] else 1


if __name__ == '__main__':
    sys.exit(main())
