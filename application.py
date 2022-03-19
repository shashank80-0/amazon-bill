from flask import Flask, render_template
from flask import request, send_file
from flask_cors import CORS

from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from pathlib import Path


app = Flask(__name__, template_folder="templates")
CORS(app)


def name_sort():
    new_file = PdfFileWriter()

    file_object = PdfFileReader("removed-blank.pdf")

    pages = file_object.getNumPages()

    sku_dict = {}
    sku_name_not_available = []

    for index in range(0, pages):

        page = file_object.getPage(index)

        page_text = page.extractText()

        totals_selector = page_text.find("Totals")

        if totals_selector > -1:
            totals_selector = int(totals_selector + 8)

        sku_selector = page_text.find("SKU:")

        if sku_selector > -1:
            sku_selector = int(sku_selector - 1)

        if totals_selector > -1 and sku_selector > -1:

            sku_name = page_text[totals_selector:sku_selector]

            if sku_name:
                sku_name = sku_name.replace("\n", " ")
                sku_dict[index] = sku_name
            else:
                sku_dict[index] = str(sku_dict.get(index - 1))
        else:
            sku_name_not_available.append(index)
            sku_dict[index] = str(sku_dict.get(index - 1))

    sku_id_list = list(set(sku_dict.values()))

    sku_id_list.sort()

    all_pages_list = []

    for sku in sku_id_list:
        sku_pages = [i for i, j in sku_dict.items() if j == sku]

        all_pages_list.extend(sku_pages)

        for sku_page in sku_pages:
            new_file.addPage(file_object.getPage(int(sku_page)))

    with Path("sorted.pdf").open(mode="wb") as output_file:
        new_file.write(output_file)


def remove_blank():
    new_file = PdfFileWriter()
    file_object = PdfFileReader("merged.pdf")

    pages = file_object.getNumPages()

    blank_pages = []

    for index in range(0, pages):

        page = file_object.getPage(index)

        page_text = page.extractText()

        if len(page_text) == 0:
            blank_pages.append(index)

    for index in range(0, pages):
        page = file_object.getPage(index)
        page_text = page.extractText()
        if index not in blank_pages:

            new_file.addPage(file_object.getPage(index))

    with Path("removed-blank.pdf").open(mode="wb") as output_file:
        new_file.write(output_file)


def merge(all_files):
    mergeFile = PdfFileMerger()

    for file in all_files:
        mergeFile.append(PdfFileReader(file, "rb"))

    mergeFile.write("merged.pdf")


def downloadFile():
    path = "sorted.pdf"
    return send_file(path, as_attachment=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploadfile/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":

        all_files = request.files.getlist("inputFile")

        merge(all_files=all_files)
        remove_blank()
        name_sort()
        return downloadFile()


if __name__ == "__main__":
    app.run()
