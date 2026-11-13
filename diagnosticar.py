from promptvideo.diagnostics import diagnosticar
import json
print(json.dumps(diagnosticar(), ensure_ascii=False, indent=2))
