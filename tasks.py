from robocorp.tasks import task
from robocorp import browser
from RPA.Tables import Tables
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    orders = get_orders()
    fill_the_form(orders)
    archive_receipts()

def open_robot_order_website():
    """Opens https://robotsparebinindustries.com/#/robot-order"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")
    close_annoying_modal()

def get_orders():
    """Reads content of https://robotsparebinindustries.com/orders.csv"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", target_file="output/orders.csv", overwrite=True)
    table = Tables()
    return table.read_table_from_csv("output/orders.csv", header=True)

def fill_the_form(orders):
    """Inputs orders from csv"""
    open_robot_order_website()

    for row in orders:
        input_order(row)
        
def input_order(row):
    """Inputs a single order from csv row"""
    close_annoying_modal()
    page = browser.page()
    page.select_option("#head", row["Head"])
    page.click("#id-body-" + row["Body"])
    page.fill("//input[contains(@placeholder,'Enter the part number for the legs')]", row["Legs"])
    page.fill("#address", row["Address"])
    page.click("#preview")
    page.click("#order")
    order_successful = False

    while order_successful != True:
        order_successful = submit_order(row["Order number"])

def submit_order(order_number):
    """Submits https://robotsparebinindustries.com/#/robot-order order and handles errors"""
    page = browser.page()
    close_annoying_modal()

    if page.is_visible("//div[contains(@class, 'alert alert-danger')]"):
        page.click("#order")
        return False
    else:
        screenshot_path = screenshot_robot(order_number)
        receipt_path = store_receipt_as_pdf(order_number)
        embed_screenshot_to_receipt(screenshot_path, receipt_path)
        page.click("#order-another")
        return True

def close_annoying_modal():
    """Closes https://robotsparebinindustries.com/#/robot-order pop-up"""
    page = browser.page()

    if page.is_visible("//div[contains(@class, 'alert-buttons')]"):
        page.click("button:text('OK')")

def store_receipt_as_pdf(order_number):
    """Stores order receipt as PDF"""
    pdf = PDF()
    page = browser.page()
    receipt_html = page.locator("#order-completion").inner_html()
    pdf.html_to_pdf(receipt_html, "output/receipts/" + order_number + "_receipt.pdf")
    return "output/receipts/" + order_number + "_receipt.pdf"

def screenshot_robot(order_number):
    """Stores a screenshot of robot"""
    page = browser.page()
    page.locator("#robot-preview-image").screenshot(path="output/images/" + order_number + "_screenshot.png")
    return "output/images/" + order_number + "_screenshot.png"

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Adds screenshot to PDF"""
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(image_path=screenshot, source_path=pdf_file, output_path=pdf_file)

def archive_receipts():
    """Add PDFs into a ZIP file"""
    lib = Archive()
    lib.archive_folder_with_zip(folder="output/receipts", archive_name="output/receipts.zip")