# main/utils.py

import uuid
import os
from io import BytesIO
import boto3
import requests
from dotenv import load_dotenv
from .models import PDFResult
from PIL import Image as PILImage
# ReportLab kutubxonasi importlari
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, KeepTogether, Flowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Agar LotusCoder shriftidan foydalanmoqchi bo'lsangiz, uni ro'yxatga oling:
# pdfmetrics.registerFont(TTFont('LotusCoder', '/path/to/Lotuscoder-0WWrG.ttf'))
default_font = 'Helvetica'  # yoki 'LotusCoder' agar ro'yxatga olingan bo'lsa

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_REGION_NAME') or 'us-east-1'


# Gorizontal chiziq (separator) chizish uchun maxsus Flowable
class HR(Flowable):
    def __init__(self, width, thickness=1, color=colors.black):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        self.height = thickness

    def draw(self):
        self.canv.setLineWidth(self.thickness)
        self.canv.setStrokeColor(self.color)
        self.canv.line(0, 0, self.width, 0)


def generate_pdf(data):

    image_src = data['image']

    # Har xil kategoriyalarga ajratish va ballarni hisoblash
    majburiy_results = []
    fan1_results = []
    fan2_results = []
    majburiy_total = 0.0
    fan1_total = 0.0
    fan2_total = 0.0

    for test in data["results"]:
        category = test.get("category", "")
        status = str(test.get("status", "")).lower()
        if category.startswith("Majburiy_fan"):
            majburiy_results.append(test)
            if status == "true":
                majburiy_total += 1.1
        elif category.startswith("Fan_1"):
            fan1_results.append(test)
            if status == "true":
                fan1_total += 3.1
        elif category.startswith("Fan_2"):
            fan2_results.append(test)
            if status == "true":
                fan2_total += 2.1

    overall_total = majburiy_total + fan1_total + fan2_total

    # Ro'yxatlarni 'number' bo'yicha tartiblash
    majburiy_results = sorted(majburiy_results, key=lambda x: int(x.get('number', 0)))
    fan1_results = sorted(fan1_results, key=lambda x: int(x.get('number', 0)))
    fan2_results = sorted(fan2_results, key=lambda x: int(x.get('number', 0)))

    # ReportLab uslublari
    styles = getSampleStyleSheet()
    font_name = default_font

    header_style = ParagraphStyle('Header', parent=styles['Heading2'], alignment=1, fontName=font_name)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName=font_name)
    result_style = ParagraphStyle('Result', parent=normal_style, fontSize=10, fontName=font_name)
    total_style = ParagraphStyle('Total', parent=normal_style, fontSize=11, alignment=1, fontName=font_name)
    footer_style = ParagraphStyle('Footer', parent=styles['Heading3'], alignment=1, fontName=font_name)

    # Rasmni URL orqali yuklab olish
    try:
        response = requests.get(image_src)
        response.raise_for_status()
        image_data = BytesIO(response.content)
    except Exception as e:
        image_data = None

    # PDF faylini xotiradagi buffer ga yozish uchun
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                            rightMargin=28, leftMargin=28,
                            topMargin=28, bottomMargin=28)
    story = []

    # Header: ID va telefon raqami
    story.append(Paragraph(f"ID: {data['id']}", header_style))
    story.append(Paragraph(f"Telefon: {data['phone']}", header_style))
    story.append(Spacer(1, 12))
    story.append(HR(doc.width))
    story.append(Spacer(1, 12))

    # Har bir kategoriya uchun natijalarni flowable shaklida yaratish funksiyasi
    def build_results_flowables(results, total):
        flowables = []
        for test in results:
            status = str(test.get("status", "")).lower()
            symbol = "✅" if status == "true" else "❌"
            text = f"<b>{test.get('number')}</b>. {test.get('option')} {symbol}"
            flowables.append(Paragraph(text, result_style))
            flowables.append(Spacer(1, 2))
        flowables.append(Paragraph(f"Jami: {total:.1f}", total_style))
        return flowables

    result_columns = []
    if majburiy_results:
        majburiy_flowables = build_results_flowables(majburiy_results, majburiy_total)
        result_columns.append(KeepTogether(majburiy_flowables))
    if fan1_results:
        fan1_flowables = build_results_flowables(fan1_results, fan1_total)
        result_columns.append(KeepTogether(fan1_flowables))
    if fan2_results:
        fan2_flowables = build_results_flowables(fan2_results, fan2_total)
        result_columns.append(KeepTogether(fan2_flowables))

    results_table = None
    if result_columns:
        n_cols = len(result_columns)
        available_width = doc.width
        results_col_width = available_width * 0.4
        col_width = results_col_width / n_cols
        results_table = Table([result_columns], colWidths=[col_width] * n_cols)
        results_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 0, colors.white),
            ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
        ]))

    # Rasmni PDF ga qo'shamiz
    if image_data:
        image_data.seek(0)  # Fayl boshiga qaytamiz
        try:
            pil_img = PILImage.open(image_data)
            actual_width, actual_height = pil_img.size
            ratio = actual_height / actual_width if actual_width else 1
        except Exception as e:
            ratio = 1  # Agar xatolik yuz bersa, default qiymat
        
        img = Image(image_data)
        available_width = doc.width * 0.6  # Sahifaning 60% qismi
        img.drawWidth = available_width
        calculated_height = available_width * ratio
        max_image_height = doc.height * 0.9  # Sahifaning 90% balandligi
        img.drawHeight = min(calculated_height, max_image_height)
    else:
        img = Spacer(1, 1)

    # Rasm va natijalar yonma-yon joylashishi uchun jadval
    main_table = Table([[img, results_table]],
                       colWidths=[doc.width * 0.6, doc.width * 0.4])
    main_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(main_table)
    story.append(Spacer(1, 24))

    # Footer: Umumiy natija
    story.append(Paragraph(f"Umumiy natija: {overall_total:.1f}", footer_style))

    doc.build(story)
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    # Yaratilgan PDF fayl uchun noyob nom
    random_filename = f"pdf-results/{uuid.uuid4()}.pdf"
    pdf_file_obj = BytesIO(pdf_bytes)

    # boto3 yordamida S3 ga yuklash
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION_NAME
    )
    s3_client.upload_fileobj(
        pdf_file_obj,
        AWS_STORAGE_BUCKET_NAME,
        random_filename,
        ExtraArgs={'ContentType': 'application/pdf'}
    )
    pdf_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{random_filename}"

    # PDFResult modeliga PDF URL yozish
    PDFResult.objects.create(
        user_id=data['id'],
        phone=data['phone'],
        pdf_url=pdf_url
    )

    return pdf_url
