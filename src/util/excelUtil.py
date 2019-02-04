
class ExcelUtil(object):

    @staticmethod
    def excel_append_rows(rows, filename="test_results.xlsx"):
        import openpyxl

        book = openpyxl.load_workbook(filename)
        sheet = book.active

        for row in rows:
            sheet.append(row)

        sheet.append(row)
        book.save(filename)
    
    @staticmethod
    def excel_append_row(row, filename="test_results.xlsx"):
        import openpyxl

        book = openpyxl.load_workbook(filename)
        sheet = book.active

        sheet.append(row)
        book.save(filename)

    @staticmethod
    def get_computer_hostname():
        import socket
        hostname = socket.gethostname()
        return hostname

    @staticmethod
    def get_datetime_str():
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")