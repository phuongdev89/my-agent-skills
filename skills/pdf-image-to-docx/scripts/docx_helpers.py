# -*- coding: utf-8 -*-
"""
docx_helpers.py
Bộ thư viện helper chuẩn hóa dùng cho việc tạo, định dạng và dàn trang DOCX từ ảnh/PDF.
Bao gồm:
- Thiết lập trang A4 chuẩn, căn lề 0.75 inch, làm sạch header/footer chống rò rỉ văn bản.
- XML cell shading, cell margins, cell borders.
- Heading 1 (Chương / Phần) & Heading 2 (Banner có màu nền) hiển thị chuẩn trên Left Navigation Pane.
- Các hàm dựng bảng, ma trận đối chiếu (Comparison Cards), sơ đồ quy trình (Process Steps), hộp chỉ số (Stat Boxes), hộp Callout đen (QR Code / Link).
- Kiểm soát ngắt trang tường minh (Explicit PageBreak).
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

# --- XML CELL STYLING ---

def set_cell_shd(cell, color_hex):
    """Đặt màu nền cho một ô bảng (VD: 'E2E8F0', 'EFF6FF', '0F172A')."""
    cell._tc.get_or_add_tcPr().append(
        parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    )

def set_cell_mar(cell, top=120, bottom=120, left=150, right=150):
    """Đặt lề trong (padding) cho ô bảng theo đơn vị dxa (20 dxa = 1 pt)."""
    cell._tc.get_or_add_tcPr().append(
        parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            f'<w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/>'
            f'</w:tcMar>'
        )
    )

def set_cell_border(cell, top=None, bottom=None, left=None, right=None):
    """
    Đặt viền cho ô bảng.
    Mỗi tham số có thể là None (không viền) hoặc dict chứa:
    {'val': 'single', 'sz': '4', 'color': 'CBD5E1'}
    """
    tcPr = cell._tc.get_or_add_tcPr()
    borders = ['<w:tcBorders ' + nsdecls("w") + '>']
    for side, b in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        if b is None:
            borders.append(f'<w:{side} w:val="none"/>')
        else:
            val = b.get('val', 'single')
            sz = b.get('sz', '4')
            col = b.get('color', 'auto')
            borders.append(f'<w:{side} w:val="{val}" w:sz="{sz}" w:space="0" w:color="{col}"/>')
    borders.append('</w:tcBorders>')
    tcPr.append(parse_xml(''.join(borders)))

# --- DOCUMENT SETUP (ENVELOPE C5 & NARROW MARGINS) ---

CONTENT_WIDTH_INCHES = 5.38 # Khổ C5 rộng 6.38" trừ lề Narrow 0.5" x 2 = 5.38" (136.6 mm)

def setup_document_c5_narrow(doc, font_name='Arial', base_font_size=10):
    """
    Cấu hình kích thước Envelope C5 (162mm x 229mm), lề Narrow (0.5 inch / 12.7mm),
    làm sạch header/footer chống rò rỉ văn bản và cấu hình Normal style.
    """
    from docx.shared import Mm
    for section in doc.sections:
        section.page_width = Mm(162)   # Envelope C5: 162 mm (6.38 in)
        section.page_height = Mm(229)  # Envelope C5: 229 mm (9.02 in)
        section.top_margin = Inches(0.5)    # Narrow: 0.5 in (12.7 mm)
        section.bottom_margin = Inches(0.5) # Narrow: 0.5 in (12.7 mm)
        section.left_margin = Inches(0.5)   # Narrow: 0.5 in (12.7 mm)
        section.right_margin = Inches(0.5)  # Narrow: 0.5 in (12.7 mm)
        section.different_first_page_header_footer = False

        # Xóa sạch header/footer mặc định để tuyệt đối không rò rỉ text
        header = section.header
        header.is_linked_to_previous = False
        for p in header.paragraphs:
            p.text = ""
        footer = section.footer
        footer.is_linked_to_previous = False
        for p in footer.paragraphs:
            p.text = ""

    normal_style = doc.styles['Normal']
    normal_style.font.name = font_name
    normal_style.font.size = Pt(base_font_size)
    normal_style.font.color.rgb = RGBColor(30, 41, 59) # Slate 800
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)
    return doc

def setup_document_a4(doc, font_name='Arial', base_font_size=10):
    """Alias chuyển tiếp: luôn áp dụng Envelope C5 và lề Narrow theo quy chuẩn mới."""
    return setup_document_c5_narrow(doc, font_name=font_name, base_font_size=base_font_size)

# --- PARAGRAPH & HEADING HELPERS ---

def add_chapter_title(doc, number_str, title_str, badge_bg="1E3A8A", badge_color="FFFFFF"):
    """
    Tạo tiêu đề Chương / Phần chuẩn Heading 1:
    - Có badge số chương nổi bật.
    - Tiêu đề in hoa đậm hiển thị chính xác trên Word Navigation Pane.
    """
    # 1. Badge số chương dạng bảng nhỏ gọn
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    cell = tbl.cell(0, 0)
    set_cell_shd(cell, badge_bg)
    set_cell_mar(cell, top=60, bottom=60, left=120, right=120)
    set_cell_border(cell)
    cell.width = Inches(1.8)
    p_badge = cell.paragraphs[0]
    p_badge.paragraph_format.space_after = Pt(0)
    p_badge.paragraph_format.line_spacing = 1.0
    r_badge = p_badge.add_run(number_str.upper())
    r_badge.font.name = 'Arial'
    r_badge.font.size = Pt(9.5)
    r_badge.font.bold = True
    r_badge.font.color.rgb = RGBColor(255, 255, 255)

    # 2. Dòng tiêu đề chính (Heading 1)
    p_title = doc.add_paragraph(style='Heading 1')
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(14)
    r_title = p_title.add_run(f"{number_str.upper()}: {title_str.upper()}")
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(16)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    return p_title

def add_heading_2_banner(doc, title_str, bg_hex="E2E8F0", text_color="0F172A"):
    """
    Tạo đề mục Heading 2 dạng thanh banner có màu nền:
    - Hiển thị trên Navigation Pane của Word.
    - Căn giữa hoặc lề trái, viền mỏng tinh tế.
    """
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shd(cell, bg_hex)
    set_cell_mar(cell, top=100, bottom=100, left=160, right=160)
    set_cell_border(cell,
                    top={'val': 'single', 'sz': '4', 'color': 'CBD5E1'},
                    bottom={'val': 'single', 'sz': '6', 'color': '94A3B8'},
                    left=None, right=None)
    cell.width = Inches(CONTENT_WIDTH_INCHES) # Chiều rộng vùng nội dung trang Envelope C5 lề Narrow (5.38")

    p = cell.paragraphs[0]
    p.style = doc.styles['Heading 2']
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    r = p.add_run(title_str.upper())
    r.font.name = 'Arial'
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = RGBColor.from_string(text_color)
    
    # Khoảng đệm sau bảng banner
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(4)
    return tbl

def add_body_p(doc, runs_tuples, space_after=6, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.LEFT):
    """
    Thêm đoạn văn với danh sách các run tùy biến.
    runs_tuples: danh sách các tuple: (text, bold_bool, italic_bool, RGBColor_or_None, font_size_pt_or_None)
    """
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    p.alignment = align
    for item in runs_tuples:
        text = item[0]
        bold = item[1] if len(item) > 1 else False
        italic = item[2] if len(item) > 2 else False
        color = item[3] if len(item) > 3 else None
        size = item[4] if len(item) > 4 else None

        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.bold = bold
        r.font.italic = italic
        if color is not None:
            r.font.color.rgb = color
        if size is not None:
            r.font.size = Pt(size)
    return p

def add_bullet_p(doc, runs_tuples, space_after=4, bullet_char="• "):
    """Thêm một dòng bullet list định dạng đẹp, thụt đầu dòng chuẩn."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15

    r_bullet = p.add_run(bullet_char)
    r_bullet.font.name = 'Arial'
    r_bullet.font.bold = True
    r_bullet.font.color.rgb = RGBColor(37, 99, 235) # Blue 600

    for item in runs_tuples:
        text = item[0]
        bold = item[1] if len(item) > 1 else False
        italic = item[2] if len(item) > 2 else False
        color = item[3] if len(item) > 3 else None

        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.bold = bold
        r.font.italic = italic
        if color is not None:
            r.font.color.rgb = color
    return p

# --- VISUAL RECREATION HELPERS (TABLES & CALLOUTS) ---

def add_qr_callout(doc, text_runs, bg_hex="0F172A", text_color="FFFFFF"):
    """Tạo hộp Callout nền tối (đen/xanh thẫm) bo góc cho QR Code hoặc liên kết tài nguyên."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shd(cell, bg_hex)
    set_cell_mar(cell, top=140, bottom=140, left=180, right=180)
    set_cell_border(cell)
    cell.width = Inches(CONTENT_WIDTH_INCHES)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    for item in text_runs:
        text = item[0]
        bold = item[1] if len(item) > 1 else False
        italic = item[2] if len(item) > 2 else False
        color = item[3] if len(item) > 3 else RGBColor.from_string(text_color)
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(6)
    return tbl

def add_comparison_cards(doc, left_card, right_card):
    """
    Tạo bảng so sánh 2 cột đối chiếu (Ví dụ: Sai vs Đúng, Reup vs Remake, Trước vs Sau).
    Mỗi card là một dict:
    {
        'badge': '❌ REUP',
        'badge_bg': 'FEE2E2',
        'badge_color': '991B1B',
        'title': 'Copy nguyên video',
        'points': ['Nguy cơ mất kênh', 'Không học được kỹ năng', ...]
    }
    """
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    for idx, (cell, card) in enumerate(zip(tbl.rows[0].cells, [left_card, right_card])):
        cell.width = Inches(CONTENT_WIDTH_INCHES / 2)
        set_cell_shd(cell, card.get('bg_hex', 'F8FAFC'))
        border_col = card.get('border_color', 'CBD5E1')
        set_cell_border(cell,
                        top={'val': 'single', 'sz': '6', 'color': border_col},
                        bottom={'val': 'single', 'sz': '6', 'color': border_col},
                        left={'val': 'single', 'sz': '6', 'color': border_col},
                        right={'val': 'single', 'sz': '6', 'color': border_col})
        set_cell_mar(cell, top=140, bottom=140, left=140, right=140)

        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(4)
        r_badge = p.add_run(card.get('badge', ''))
        r_badge.font.name = 'Arial'
        r_badge.font.bold = True
        r_badge.font.size = Pt(10)
        badge_rgb = card.get('badge_color', '0F172A')
        r_badge.font.color.rgb = RGBColor.from_string(badge_rgb)

        if card.get('title'):
            p_t = cell.add_paragraph()
            p_t.paragraph_format.space_after = Pt(6)
            r_t = p_t.add_run(card.get('title'))
            r_t.font.name = 'Arial'
            r_t.font.bold = True
            r_t.font.size = Pt(9.5)
            r_t.font.color.rgb = RGBColor(15, 23, 42)

        for pt in card.get('points', []):
            p_pt = cell.add_paragraph()
            p_pt.paragraph_format.space_after = Pt(3)
            p_pt.paragraph_format.line_spacing = 1.1
            r_dot = p_pt.add_run("• ")
            r_dot.font.bold = True
            r_dot.font.color.rgb = RGBColor.from_string(badge_rgb)
            r_text = p_pt.add_run(pt)
            r_text.font.name = 'Arial'
            r_text.font.size = Pt(9)
            r_text.font.color.rgb = RGBColor(51, 65, 85)

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(6)
    return tbl

def add_process_steps(doc, steps_list):
    """
    Tạo quy trình ngang từng bước (Bước 1 → Bước 2 → Bước 3...).
    steps_list: danh sách các dict {'num': '1', 'title': 'CHỌN SÁCH', 'desc': 'Ngách ngách rộng...'}
    """
    n_cols = len(steps_list)
    tbl = doc.add_table(rows=1, cols=n_cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    col_w = Inches(CONTENT_WIDTH_INCHES / n_cols)

    for idx, (cell, step) in enumerate(zip(tbl.rows[0].cells, steps_list)):
        cell.width = col_w
        set_cell_shd(cell, "F1F5F9" if idx % 2 == 0 else "E2E8F0")
        set_cell_mar(cell, top=120, bottom=120, left=100, right=100)
        set_cell_border(cell,
                        top={'val': 'single', 'sz': '4', 'color': 'CBD5E1'},
                        bottom={'val': 'single', 'sz': '6', 'color': '3B82F6'},
                        left=None, right=None)

        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r_num = p.add_run(f"BƯỚC {step.get('num', idx+1)}\n")
        r_num.font.name = 'Arial'
        r_num.font.bold = True
        r_num.font.size = Pt(8.5)
        r_num.font.color.rgb = RGBColor(37, 99, 235)

        r_title = p.add_run(f"{step.get('title', '')}\n")
        r_title.font.name = 'Arial'
        r_title.font.bold = True
        r_title.font.size = Pt(9)
        r_title.font.color.rgb = RGBColor(15, 23, 42)

        if step.get('desc'):
            r_desc = p.add_run(step.get('desc'))
            r_desc.font.name = 'Arial'
            r_desc.font.size = Pt(8)
            r_desc.font.color.rgb = RGBColor(71, 85, 105)

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(6)
    return tbl

def add_stat_boxes(doc, stats_list):
    """
    Tạo các ô hiển thị chỉ số nổi bật (KPI / Thống kê kết quả).
    stats_list: danh sách các tuple: (số_lớn, nhãn_mô_tả, icon)
    Ví dụ: [("35", "TỔNG VIDEO", "▶️"), ("12.400", "LƯỢT XEM", "👁️"), ...]
    """
    n_cols = len(stats_list)
    tbl = doc.add_table(rows=1, cols=n_cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    col_w = Inches(CONTENT_WIDTH_INCHES / n_cols)

    for cell, item in zip(tbl.rows[0].cells, stats_list):
        cell.width = col_w
        set_cell_shd(cell, "F8FAFC")
        set_cell_mar(cell, top=140, bottom=140, left=80, right=80)
        set_cell_border(cell,
                        top={'val': 'single', 'sz': '4', 'color': 'E2E8F0'},
                        bottom={'val': 'single', 'sz': '8', 'color': '2563EB'},
                        left={'val': 'single', 'sz': '4', 'color': 'E2E8F0'},
                        right={'val': 'single', 'sz': '4', 'color': 'E2E8F0'})

        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)

        val_str = item[0]
        label_str = item[1]
        icon_str = item[2] if len(item) > 2 else ""

        if icon_str:
            r_ic = p.add_run(f"{icon_str} ")
            r_ic.font.size = Pt(11)

        r_val = p.add_run(f"{val_str}\n")
        r_val.font.name = 'Arial'
        r_val.font.bold = True
        r_val.font.size = Pt(13)
        r_val.font.color.rgb = RGBColor(30, 58, 138)

        r_lbl = p.add_run(label_str.upper())
        r_lbl.font.name = 'Arial'
        r_lbl.font.bold = True
        r_lbl.font.size = Pt(8)
        r_lbl.font.color.rgb = RGBColor(100, 116, 139)

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(6)
    return tbl

def add_explicit_page_break(doc):
    """Thêm một ngắt trang tường minh và chuẩn hóa."""
    doc.add_page_break()
