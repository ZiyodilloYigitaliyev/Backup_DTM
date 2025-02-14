import uuid
import os
from io import BytesIO
import boto3
from weasyprint import HTML
from dotenv import load_dotenv
from .models import PDFResult

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_REGION_NAME') or 'us-east-1'

def generate_pdf(data):
    image_src = data['image']

    # Natijalarni ajratamiz va jami hisoblaymiz
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

    # Ro'yxatlarni tartiblash
    majburiy_results.sort(key=lambda x: int(x.get('number', 0)))
    fan1_results.sort(key=lambda x: int(x.get('number', 0)))
    fan2_results.sort(key=lambda x: int(x.get('number', 0)))

    def build_results_html(results):
        html = ""
        for test in results:
            status = str(test.get("status", "")).lower()
            if status == "true":
                symbol = '<img src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/chekvector.png" alt="True">'
            else:
                symbol = '<img src="https://scan-app-uploads.s3.eu-north-1.amazonaws.com/tru-folse-images/crossvector.png" alt="False">'
            html += f'<div class="result"><strong>{test.get("number")}.</strong> {test.get("option")} {symbol}</div>'
        return html

    def build_category_html(title, results, total):
        if not results:
            return ""
        html = f'<div class="category-column"><h4>{title}</h4>'
        html += build_results_html(results)
        html += f'<div class="total">Jami: {total:.1f}</div></div>'
        return html

    # Har bir kategoriya uchun ustunlar
    cat1_html = build_category_html("Majburiy fan", majburiy_results, majburiy_total)
    cat2_html = build_category_html("Fan 1", fan1_results, fan1_total)
    cat3_html = build_category_html("Fan 2", fan2_results, fan2_total)
    # Yonma-yon chiqishi uchun flex konteyneri
    categories_html = f'<div class="categories">{cat1_html}{cat2_html}{cat3_html}</div>'

    html_content = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        @page {{
          size: A4;
          margin: 10mm;
        }}
        body {{
          font-family: Arial, sans-serif;
          color: #333;
          margin: 0;
          padding: 0;
        }}
        .header, .footer {{
          text-align: center;
          padding: 10px;
          background: #f0f0f0;
          border: 1px solid #ccc;
        }}
        .content {{
          display: flex;
          width: 100%;
          box-sizing: border-box;
        }}
        .left {{
          width: 60%;
          padding: 10px;
        }}
        .right {{
          width: 40%;
          padding: 10px;
        }}
        /* Kategoriya ustunlarini yonma-yon joylashtirish */
        .categories {{
          display: flex;
          justify-content: space-between;
        }}
        .category-column {{
          width: 32%;
          box-sizing: border-box;
        }}
        .result {{
          margin: 5px 0;
          font-size: 14px;
        }}
        .result img {{
          width: 12px;
          height: 12px;
          vertical-align: middle;
        }}
        .total {{
          text-align: right;
          font-weight: bold;
          font-size: 16px;
          margin-top: 10px;
        }}
      </style>
    </head>
    <body>
      <div class="header">
         <h2>ID: {data['id']}</h2>
         <p>Telefon: {data['phone']}</p>
      </div>
      <div class="content">
         <div class="left">
           <img src="{image_src}" alt="Rasm">
         </div>
         <div class="right">
           {categories_html}
         </div>
      </div>
      <div class="footer">
         <h3>Umumiy natija: {overall_total:.1f}</h3>
      </div>
    </body>
    </html>
    """

    # PDF yaratish va S3 ga yuklash
    pdf_bytes = HTML(string=html_content, base_url=".").write_pdf()
    random_filename = f"pdf-results/{uuid.uuid4()}.pdf"
    pdf_file_obj = BytesIO(pdf_bytes)

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

    PDFResult.objects.create(
         user_id=data['id'],
         phone=data['phone'],
         pdf_url=pdf_url
    )

    return pdf_url
