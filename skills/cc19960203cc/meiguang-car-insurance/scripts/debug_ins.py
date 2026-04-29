import sys; sys.path.insert(0, '.')
from run_extract import parse_pdf, RESULTS
import openpyxl, os

wb = openpyxl.load_workbook(r'C:\Users\Administrator\Desktop\车险保单提取结果_v5.xlsx')
ws = wb.active
folder = r'C:\Users\Administrator\Desktop\车险保单'

print('RESULTS so far:', len(RESULTS))

for row in [48, 51]:
    fname = ws.cell(row,1).value
    print()
    print('=== Row%d: fname=%r ===' % (row, str(fname)[:50]))
    
    # Find the file
    matching = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')]
    if not matching:
        matching = [f for f in os.listdir(folder) if '司乘' in f]
    
    for mf in matching[:5]:
        p = os.path.join(folder, mf)
        print()
        print('Testing:', mf)
        result = parse_pdf(p)
        print('  保险起期: %r' % result.get('保险起期',''))
        print('  文件名: %r' % result.get('文件名',''))
        print('  保险公司: %r' % result.get('保险公司名称',''))
        print('  RESULTS count:', len(RESULTS))
        # Check if filename matches
        excel_fname = str(fname)
        result_fname = str(result.get('文件名',''))
        print('  Excel fname:', repr(excel_fname[:50]))
        print('  Result fname:', repr(result_fname[:50]))
        print('  Match:', excel_fname == result_fname)
    break
