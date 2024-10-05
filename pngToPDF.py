import os
from PIL import Image
from fpdf import FPDF
import argparse

# 1ページに配置する画像の数
IMAGES_PER_PAGE = 5

# ディレクトリ内のpngファイルを分類して収集
def collect_png_files(directory, all_mode):
    categories = {
        'abura': [],
        'kiku': [],
        'momoziro': [],
        'yubi': []
    }
    all_files = []

    for filename in os.listdir(directory):
        if filename.endswith('.png'):
            file_path = os.path.join(directory, filename)
            if all_mode:  # -Aオプションが指定された場合、すべてのファイルを処理
                all_files.append(file_path)
            else:  # ファイル名に基づいて分類
                if 'abura' in filename:
                    categories['abura'].append(file_path)
                elif 'kiku' in filename:
                    categories['kiku'].append(file_path)
                elif 'momoziro' in filename:
                    categories['momoziro'].append(file_path)
                elif 'yubi' in filename:
                    categories['yubi'].append(file_path)

    if all_mode:
        return {'all': all_files}
    return categories

# PNGファイルをPDFに変換し、1ページに複数の画像を配置
def create_pdf(category, image_paths, output_pdf_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for i in range(0, len(image_paths), IMAGES_PER_PAGE):
        pdf.add_page()
        
        # ページ内に最大5つの画像を配置
        for j, image_path in enumerate(image_paths[i:i + IMAGES_PER_PAGE]):
            image = Image.open(image_path)
            width, height = image.size
            aspect_ratio = height / width
            
            # PDFの幅に合わせた画像サイズ調整 (1列の画像の幅は約180mm)
            image_width = 180
            image_height = int(image_width * aspect_ratio)

            # PDF上の画像配置位置
            x_offset = 10
            y_offset = 20 + j * (image_height + 5)  # 画像間に5mmの余白
            
            # 画像をPDFに挿入
            pdf.image(image_path, x=x_offset, y=y_offset, w=image_width)

    # PDFとして保存
    pdf.output(output_pdf_path)
    print(f"PDF saved to {output_pdf_path}")

# 画像ファイルの収集とPDF生成
def generate_pdfs(input_directory, all_mode):
    # 画像ファイルを収集
    categories = collect_png_files(input_directory, all_mode)

    # pdf_resultsフォルダがなければ作成
    output_directory = os.path.join(input_directory, 'pdf_results')
    os.makedirs(output_directory, exist_ok=True)

    # 各カテゴリに対応するPDFを生成
    for category, image_paths in categories.items():
        if image_paths:
            output_pdf_path = os.path.join(output_directory, f"{category}_images.pdf")
            create_pdf(category, image_paths, output_pdf_path)

# メイン処理
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate PDFs from PNG files.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input directory containing PNG files.')
    parser.add_argument('-A', '--all', action='store_true', help='Process all PNG files in the directory regardless of filenames.')
    args = parser.parse_args()

    input_directory = args.input
    all_mode = args.all

    if os.path.isdir(input_directory):
        generate_pdfs(input_directory, all_mode)
    else:
        print(f"Error: {input_directory} is not a valid directory.")