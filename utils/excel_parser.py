# # utils/excel_parser.py

# import pandas as pd

# def parse_excel(file) -> str:
#     all_sheets = pd.read_excel(file, sheet_name=None, header=None)
#     output = []

#     for sheet_name, df in all_sheets.items():
#         output.append(f"=== SHEET: {sheet_name} ===")
#         df = df.dropna(how="all").fillna("")
#         output.append(df.to_csv(index=False, header=False))

#     return "\n".join(output)


# utils/excel_parser.py

import pandas as pd

def parse_excel(file) -> dict:
    all_sheets = pd.read_excel(file, sheet_name=None, header=None)
    result = {}

    for sheet_name, df in all_sheets.items():
        df = df.dropna(how="all").fillna("")
        result[sheet_name] = df.to_csv(index=False, header=False)

    return result