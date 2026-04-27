from datetime import datetime
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill
from decimal import Decimal


def export_to_excel(headers, file_name, queryset, formatters=None, title=None):

    """
    Create an HttpResponse that serves a Excel file.

    Args:
        headers (List[str]): Header row names.
        field_names (List[str]): Fields to extract from queryset.
        queryset (QuerySet): Django queryset to export.
        formatters (Dict[int, Callable]): Optional dict to format certain column indexes.

    Returns:
        HttpResponse: A downloadable Excel file response.
    """

    filename = f"{file_name}{datetime.today()}.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb = Workbook()
    ws = wb.active
    if title:
        ws.title = title

    center_align = Alignment(horizontal="center", vertical="center")
    header_fill = PatternFill(start_color='FFF8CBAD', end_color='FFF8CBAD', fill_type="solid")
    header_font = Font(color="FF000000", size=14, bold=False)

    ws.append(headers)

    for col_index, _ in enumerate(headers, start=1):

        cell = ws.cell(row=1, column=col_index)
        cell.font = header_font
        cell.fill = header_fill
    

    # If queryset is already a list use it directly otherwise convert a Queryset to a list using iterator
    rows = queryset if isinstance(queryset, list) else list(queryset.iterator())

    for row in rows:
        # if the instance is tuple convert it to list to make it mutable
        if isinstance(row, tuple):
            row = list(row)

        # Apply formatters if provided
        if formatters:
            for index, func in formatters.items():
                if 0 <= index < len(row):
                    row[index] = func(row[index])

        ws.append(row)

        row_number = ws.max_row

        # Style each cell
        for col_index, value in enumerate(row, start=1):
            cell = ws.cell(row=row_number, column=col_index)


            # Apply 2-decimal format automatically to all numeric values
            if isinstance(value, (float, Decimal)):
                cell.number_format = '#,##0.00'  # 0.00 format

            cell.alignment = center_align
            

    # Add width in the columns
    for i in range(1, ws.max_column + 1):
        column_letter = get_column_letter(i)
        ws.column_dimensions[column_letter].width = 25 

    wb.save(response)
   

    return response