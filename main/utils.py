import uuid
import os
from io import BytesIO
import boto3
import requests
from dotenv import load_dotenv
from .models import PDFResult
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Flowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_REGION_NAME') or 'us-east-1'

# Standart font: kerak bo'lsa, siz o'zingizga mos fontni ro'yxatdan o'tkazishingiz mumkin
base_font = 'Helvetica'

# Gorizontal chiziq (horizontal rule) uchun maxsus Flowable
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
    # Ma'lumotlarni ajratib olamiz va umumiy hisoblarni yuritamiz
    image_src = data['image']

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

    # Ro'yxatlarni raqam bo'yicha tartiblash
    majburiy_results.sort(key=lambda x: int(x.get('number', 0)))
    fan1_results.sort(key=lambda x: int(x.get('number', 0)))
    fan2_results.sort(key=lambda x: int(x.get('number', 0)))

    # Stil va formatlash sozlamalari
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        name="Normal",
        fontName=base_font,
        fontSize=10,
        leading=12,
        textColor=colors.black,
    )
    header_style = ParagraphStyle(
        name="Header",
        fontName=base_font,
        fontSize=14,
        alignment=1,  # markazlashtirilgan
        spaceAfter=6,
        textColor=colors.black,
        leading=16
    )
    total_style = ParagraphStyle(
        name="Total",
        fontName=base_font,
        fontSize=12,
        alignment=1,
        spaceBefore=10,
        textColor=colors.black,
        leading=14
    )
    category_total_style = ParagraphStyle(
        name="CategoryTotal",
        fontName=base_font,
        fontSize=10,
        leading=12,
        spaceBefore=4,
        textColor=colors.black,
        alignment=1
    )

    # S3 URL-dagi emoji rasmlarni bir marta yuklab olamiz
    true_emoji_url = "https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/chekvector.png"
    false_emoji_url = "https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/crossvector.png"

    try:
        response_true = requests.get(true_emoji_url)
        if response_true.status_code == 200:
            true_image_bytes = response_true.content
        else:
            true_image_bytes = None
    except Exception:
        true_image_bytes = None

    try:
        response_false = requests.get(false_emoji_url)
        if response_false.status_code == 200:
            false_image_bytes = response_false.content
        else:
            false_image_bytes = None
    except Exception:
        false_image_bytes = None

    # Test natijalarini shakllantirish uchun funksiya
    def build_results_flowables(results):
        flowables = []
        for test in results:
            number = test.get('number')
            option = test.get('option')
            status = str(test.get("status", "")).lower()
            # Matn: raqam va test variantlari
            text_content = f"<b>{number}.</b> {option}"
            text_paragraph = Paragraph(text_content, normal_style)
            # Emoji uchun rasmni tanlaymiz
            if status == "true":
                img_bytes = true_image_bytes
            else:
                img_bytes = false_image_bytes
            if img_bytes:
                # Har safar yangi BytesIO obyektiga o'tkazamiz
                img_io = BytesIO(img_bytes)
                emoji_img = Image(img_io, width=12, height=12)
            else:
                emoji_img = Paragraph("", normal_style)
            # Matn va emoji rasmni yonma-yon joylashtirish uchun jadval tuzamiz
            row_data = [[text_paragraph, emoji_img]]
            result_table = Table(row_data, colWidths=[None, 15], hAlign='LEFT')
            result_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            flowables.append(result_table)
        return flowables

    # Har bir fan bo‘yicha ustunlarni tayyorlaymiz
    columns_data = []
    if majburiy_results:
        col = []
        col.extend(build_results_flowables(majburiy_results))
        col.append(Spacer(1, 4))
        col.append(Paragraph(f"Jami: {majburiy_total:.1f}", category_total_style))
        columns_data.append(col)
    if fan1_results:
        col = []
        col.extend(build_results_flowables(fan1_results))
        col.append(Spacer(1, 4))
        col.append(Paragraph(f"Jami: {fan1_total:.1f}", category_total_style))
        columns_data.append(col)
    if fan2_results:
        col = []
        col.extend(build_results_flowables(fan2_results))
        col.append(Spacer(1, 4))
        col.append(Paragraph(f"Jami: {fan2_total:.1f}", category_total_style))
        columns_data.append(col)

    # Asosiy rasmni yuklab olish va tayyorlash (PDF yuqori qismidagi katta rasm)
    try:
        response = requests.get(image_src)
        image_data = BytesIO(response.content)
        img = Image(image_data)
        desired_width = 300
        img.drawWidth = desired_width
        img.drawHeight = desired_width * img.imageHeight / img.imageWidth
    except Exception:
        img = Paragraph("Rasm yuklanmadi", normal_style)

    # Natijalar ustunlarini jadval shaklida joylaymiz (agar mavjud bo'lsa)
    results_table = None
    if columns_data:
        results_table = Table([columns_data], hAlign='LEFT')
        results_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

    # Asosiy jadval: rasm va natijalar yonma-yon
    main_table_data = [[img, results_table if results_table else ""]]
    main_table = Table(main_table_data, colWidths=[desired_width, None])
    main_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # PDF hujjatini yaratish uchun oqim (story) ro'yxatini tuzamiz
    story = []
    story.append(Paragraph(f"ID: {data['id']}", header_style))
    story.append(Paragraph(f"Telefon: {data['phone']}", normal_style))
    story.append(Spacer(1, 6))
    page_width = A4[0] - 40  # Chap va o'ng marginni hisobga olamiz
    story.append(HR(width=page_width, thickness=1, color=colors.black))
    story.append(Spacer(1, 12))
    story.append(main_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Umumiy natija: {overall_total:.1f}", total_style))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    doc.build(story)
    pdf_bytes = buffer.getvalue()

    # Yaratilgan fayl uchun noyob nom (pdf-results papkasida saqlanadi)
    random_filename = f"pdf-results/{uuid.uuid4()}.pdf"
    pdf_file_obj = BytesIO(pdf_bytes)

    # boto3 orqali PDFni S3 bucketga yuklaymiz
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

    # PDF URL ni ma'lumotlar bazasiga saqlaymiz
    PDFResult.objects.create(
        user_id=data['id'],
        phone=data['phone'],
        pdf_url=pdf_url
    )

    return pdf_url
