"""
Error Classifier — Klasifikasi error ke repair strategy yang tepat
"""

import re
from typing import Dict, List, Optional
from enum import Enum


class ErrorType(Enum):
    """Jenis error yang bisa dideteksi"""
    SYNTAX_INDENTATION = "syntax_indentation"
    SYNTAX_MISSING_COLON = "syntax_missing_colon"
    SYNTAX_GENERAL = "syntax_general"
    IMPORT_MISSING = "import_missing"
    IMPORT_DEPENDENCY_MISSING = "import_dependency_missing"
    IMPORT_CIRCULAR = "import_circular"
    CLASS_NOT_FOUND = "class_not_found"
    METHOD_MISSING = "method_missing"
    METHOD_DUPLICATE = "method_duplicate"
    NAME_NOT_DEFINED = "name_not_defined"
    RUNTIME_ERROR = "runtime_error"
    DECORATOR_ERROR = "decorator_error"
    INHERITANCE_ERROR = "inheritance_error"
    GENERIC_TYPING_ERROR = "generic_typing_error"
    IMPORT_ALIAS_ERROR = "import_alias_error"
    DOCSTRING_ERROR = "docstring_error"
    TAB_SPACE_ERROR = "tab_space_error"
    MULTI_ERROR = "multi_error"
    UNKNOWN = "unknown"


class ErrorClassifier:
    """Klasifikasi error ke jenis yang tepat"""

    def __init__(self):
        self.patterns = {
            ErrorType.SYNTAX_INDENTATION: [
                r"IndentationError",
                r"unexpected indent",
                r"expected an indented block"
            ],
            ErrorType.SYNTAX_MISSING_COLON: [
                r"invalid syntax.*:$",
                r"SyntaxError.*missing.*:"
            ],
            ErrorType.IMPORT_DEPENDENCY_MISSING: [
                r"ModuleNotFoundError",
                r"No module named"
            ],
            ErrorType.IMPORT_MISSING: [
                r"ImportError",
                r"cannot import name"
            ],
            ErrorType.IMPORT_CIRCULAR: [
                r"ImportError.*circular",
                r"circular import"
            ],
            ErrorType.CLASS_NOT_FOUND: [
                r"Class '(\w+)' not found",
                r"NameError.*class",
                r"class.*not defined"
            ],
            ErrorType.METHOD_MISSING: [
                r"Missing methods:",
                r"AttributeError.*has no attribute",
                r"method.*missing"
            ],
            ErrorType.METHOD_DUPLICATE: [
                r"duplicate method",
                r"cannot redefine",
                r"already defined"
            ],
            ErrorType.NAME_NOT_DEFINED: [
                r"NameError.*name '(\w+)' is not defined"
            ],
            ErrorType.RUNTIME_ERROR: [
                r"RuntimeError",
                r"TypeError",
                r"ValueError"
            ],
            ErrorType.DECORATOR_ERROR: [
                r"decorator",
                r"@\w+",
                r"SyntaxError.*decorator"
            ],
            ErrorType.INHERITANCE_ERROR: [
                r"inheritance",
                r"super\(\)",
                r"base class"
            ],
            ErrorType.GENERIC_TYPING_ERROR: [
                r"typing",
                r"List\[",
                r"Dict\[",
                r"Optional\["
            ],
            ErrorType.IMPORT_ALIAS_ERROR: [
                r"import.*as",
                r"alias"
            ],
            ErrorType.DOCSTRING_ERROR: [
                r'docstring',
                r'"""',
                r"'''"
            ],
            ErrorType.TAB_SPACE_ERROR: [
                r"tab",
                r"space",
                r"mixed.*indent"
            ],
            ErrorType.MULTI_ERROR: [
                r"multiple.*error",
                r"several.*error"
            ]
        }

    def classify(self, error_text: str) -> Dict:
        """
        Klasifikasi error
        Returns: {
            'type': ErrorType,
            'name': str,
            'confidence': float,
            'matched_pattern': str
        }
        """
        error_text_lower = error_text.lower()
        
        # Special case: "was never closed" - common SyntaxError
        if "was never closed" in error_text_lower or "never closed" in error_text_lower:
            return {
                "type": ErrorType.SYNTAX_GENERAL,
                "name": None,
                "confidence": 0.95,
                "matched_pattern": "was never closed"
            }
        
        # Try each pattern
        for error_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, error_text_lower, re.IGNORECASE)
                if match:
                    name = None
                    if match.groups():
                        name = match.group(1)
                    
                    # Check if multiple errors
                    if "multiple" in error_text_lower or "several" in error_text_lower:
                        return {
                            "type": ErrorType.MULTI_ERROR,
                            "name": name,
                            "confidence": 0.8,
                            "matched_pattern": pattern
                        }
                    
                    return {
                        "type": error_type,
                        "name": name,
                        "confidence": 0.9,
                        "matched_pattern": pattern
                    }
        
        # Try to extract name for unknown errors
        name_match = re.search(r"'(\w+)'", error_text)
        name = name_match.group(1) if name_match else None
        
        return {
            "type": ErrorType.UNKNOWN,
            "name": name,
            "confidence": 0.3,
            "matched_pattern": None
        }

    def get_repair_action(self, classification: Dict) -> str:
        """Dapatkan repair action berdasarkan klasifikasi"""
        error_type = classification["type"]
        name = classification.get("name")
        
        action_map = {
            ErrorType.SYNTAX_INDENTATION: "syntax_repair",
            ErrorType.SYNTAX_MISSING_COLON: "syntax_repair",
            ErrorType.SYNTAX_GENERAL: "syntax_repair",
            ErrorType.IMPORT_MISSING: "import_repair",
            ErrorType.IMPORT_DEPENDENCY_MISSING: "dependency_required",
            ErrorType.IMPORT_CIRCULAR: "import_repair",
            ErrorType.CLASS_NOT_FOUND: "class_repair",
            ErrorType.METHOD_MISSING: "method_repair",
            ErrorType.METHOD_DUPLICATE: "duplicate_repair",
            ErrorType.NAME_NOT_DEFINED: "name_repair",
            ErrorType.RUNTIME_ERROR: "runtime_repair",
            ErrorType.DECORATOR_ERROR: "syntax_repair",
            ErrorType.INHERITANCE_ERROR: "syntax_repair",
            ErrorType.GENERIC_TYPING_ERROR: "import_repair",
            ErrorType.IMPORT_ALIAS_ERROR: "import_repair",
            ErrorType.DOCSTRING_ERROR: "syntax_repair",
            ErrorType.TAB_SPACE_ERROR: "syntax_repair",
            ErrorType.MULTI_ERROR: "syntax_repair",
            ErrorType.UNKNOWN: "unknown"
        }
        
        return action_map.get(error_type, "unknown")


# Singleton
_classifier = None

def get_error_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ErrorClassifier()
    return _classifier
