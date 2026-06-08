import ast
import re
from typing import Tuple, List
from core.logger import logger


class ASTValidator:

    def clean_code(self, code: str) -> str:
        code = re.sub(r'<think>.*?</think>', '', code, flags=re.DOTALL)
        code = re.sub(r'^```(?:python|py|bash|sh)?\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n?```$', '', code, flags=re.MULTILINE)
        code = re.sub(r'^<[^>]{1,40}>\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'^</[^>]{1,40}>\n?', '', code, flags=re.MULTILINE)
        return code.strip()

    def validate_python(self, code: str) -> Tuple[bool, List[str]]:
        code = self.clean_code(code)
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, ["SyntaxError at line " + str(e.lineno) + ": " + str(e.msg)]
        errors = self._check_imports(tree)
        return len(errors) == 0, errors

    def validate_and_clean(self, code: str) -> Tuple[bool, str, List[str]]:
        cleaned = self.clean_code(code)
        try:
            ast.parse(cleaned)
            return True, cleaned, []
        except SyntaxError as e:
            return False, cleaned, ["SyntaxError at line " + str(e.lineno) + ": " + str(e.msg)]

    def _check_imports(self, tree: ast.AST) -> List[str]:
        errors = []
        stdlib = {
            "os","sys","re","json","time","datetime","pathlib","typing",
            "collections","itertools","functools","math","random","hashlib",
            "uuid","copy","io","abc","enum","logging","threading","subprocess",
            "tempfile","shutil","argparse","dataclasses","contextlib","string",
            "textwrap","traceback","warnings","inspect","types","operator",
            "asyncio","concurrent","queue","socket","struct","base64","binascii",
            "decimal","fractions","statistics","csv","configparser","sqlite3",
            "pickle","shelve","unittest","pprint","weakref","gc","platform",
            "signal","errno","glob","fnmatch","zipfile","tarfile","importlib",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    m = alias.name.split(".")[0]
                    if not self._available(m, stdlib):
                        errors.append("Module not available: " + alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                m = node.module.split(".")[0]
                if not self._available(m, stdlib):
                    errors.append("Module not available: " + node.module)
        return errors

    def _available(self, name: str, stdlib: set) -> bool:
        if name in stdlib:
            return True
        try:
            __import__(name)
            return True
        except ImportError:
            return False

    def extract_imports(self, code: str) -> List[str]:
        code = self.clean_code(code)
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        imports.append(a.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module.split(".")[0])
        except Exception:
            pass
        return list(set(imports))


ast_validator = ASTValidator()
