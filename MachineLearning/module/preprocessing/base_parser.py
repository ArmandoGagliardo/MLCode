# module/preprocessing/base_parser.py
class BaseParser:
    def parse(self, code: str) -> list[dict]:
        raise NotImplementedError("Ogni parser deve implementare 'parse()'")