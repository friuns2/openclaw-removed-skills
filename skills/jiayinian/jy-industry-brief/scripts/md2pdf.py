#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF converter for industry brief reports.
Uses reportlab for direct PDF generation with proper Chinese font support.

Usage:
    python md2pdf.py input.md [output.pdf]
    
If output.pdf is not specified, it will be generated as input.pdf
"""

import sys
import os
import re
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def register_chinese_fonts():
    """Register Chinese fonts for reportlab."""
    # Try common Chinese font paths
    font_paths = [
        # Windows
        r"C:\Windows\Fonts\simhei.ttf",  # 黑体
        r"C:\Windows\Fonts\simsun.ttc",  # 宋体
        r"C:\Windows\Fonts\msyh.ttc",    # 微软雅黑
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Songti.ttc",
        # Linux
        "/usr/share/fonts/chinese/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Chinese', font_path))
                return True
            except Exception as e:
                continue
    
    return False


def markdown_to_html(md_content):
    """Simple markdown to HTML converter for basic formatting."""
    html = md_content
    
    # Headers
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
    html = re.sub(r'\*(.+?)\*', r'<i>\1</i>', html)
    
    # Horizontal rule
    html = re.sub(r'^---$', r'<hr/>', html, flags=re.MULTILINE)
    
    return html


def parse_markdown_tables(md_content):
    """Extract tables from markdown content."""
    tables = []
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        if '|' in line and line.strip().startswith('|'):
            # Found a table
            table_rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                row_line = lines[i].strip()
                if row_line.startswith('|'):
                    row_line = row_line[1:]
                if row_line.endswith('|'):
                    row_line = row_line[:-1]
                
                # Skip separator row (contains ---)
                if '---' not in row_line:
                    cells = [cell.strip() for cell in row_line.split('|')]
                    table_rows.append(cells)
                i += 1
            
            if table_rows:
                tables.append(table_rows)
        else:
            i += 1
    
    return tables


def parse_markdown_sections(md_content):
    """Parse markdown content into sections."""
    sections = []
    lines = md_content.split('\n')
    current_section = {'title': '', 'content': [], 'table': None}
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for section header
        if line.startswith('###'):
            if current_section['content'] or current_section['table']:
                sections.append(current_section)
                current_section = {'title': '', 'content': [], 'table': None}
            current_section['title'] = line.replace('#', '').strip()
            i += 1
            continue
        
        # Check for table
        if '|' in line and line.strip().startswith('|'):
            table_rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                row_line = lines[i].strip()
                if row_line.startswith('|'):
                    row_line = row_line[1:]
                if row_line.endswith('|'):
                    row_line = row_line[:-1]
                
                if '---' not in row_line:
                    cells = [cell.strip() for cell in row_line.split('|')]
                    table_rows.append(cells)
                i += 1
            
            if table_rows:
                current_section['table'] = table_rows
            continue
        
        # Regular content
        if line.strip():
            current_section['content'].append(line)
        
        i += 1
    
    if current_section['content'] or current_section['table']:
        sections.append(current_section)
    
    return sections


def create_pdf(md_content, output_path):
    """Create PDF from markdown content."""
    if not REPORTLAB_AVAILABLE:
        print("Error: reportlab not installed. Install with: pip install reportlab")
        return False
    
    # Register Chinese fonts
    has_chinese_font = register_chinese_fonts()
    
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    if has_chinese_font:
        # Create Chinese-compatible styles
        title_style = ParagraphStyle(
            'ChineseTitle',
            parent=styles['Heading1'],
            fontName='Chinese',
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'ChineseHeading',
            parent=styles['Heading2'],
            fontName='Chinese',
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12
        )
        normal_style = ParagraphStyle(
            'ChineseNormal',
            parent=styles['Normal'],
            fontName='Chinese',
            fontSize=10,
            leading=14,
            spaceAfter=6
        )
    else:
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
    
    # Build content
    story = []
    sections = parse_markdown_sections(md_content)
    
    for section in sections:
        # Add title
        if section['title']:
            story.append(Paragraph(section['title'], heading_style))
            story.append(Spacer(1, 0.2*cm))
        
        # Add table if present
        if section['table']:
            table_data = section['table']
            table = Table(table_data, colWidths=[4*cm] * len(table_data[0]) if table_data else None)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.3*cm))
        
        # Add content
        for line in section['content']:
            # Convert basic markdown
            line_html = markdown_to_html(line)
            if has_chinese_font:
                story.append(Paragraph(line_html, normal_style))
            else:
                story.append(Paragraph(line_html, normal_style))
            story.append(Spacer(1, 0.1*cm))
        
        story.append(Spacer(1, 0.3*cm))
    
    # Build PDF
    try:
        doc.build(story)
        print(f"PDF generated successfully: {output_path}")
        return True
    except Exception as e:
        print(f"Error building PDF: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python md2pdf.py input.md [output.pdf]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = os.path.splitext(input_path)[0] + '.pdf'
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Read markdown content
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Create PDF
    success = create_pdf(md_content, output_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
