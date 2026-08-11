import sys
import traceback

sys.path.insert(0, r'D:\medigenie\backend')

try:
    import main
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
    print('IMPORT_FAIL')
