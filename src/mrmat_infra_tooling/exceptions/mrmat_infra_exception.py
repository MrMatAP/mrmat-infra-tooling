
class MrMatInfraException(Exception):

    def __init__(self, code: int = 500, msg: str = "An error has occurred"):
        self._code = code
        self._msg = msg

    @property
    def code(self) -> int:
        return self._code

    @property
    def msg(self) -> str:
        return self._msg

    def __str__(self) -> str:
        return f"[{self.code}] {self.msg}"

    def __repr__(self) -> str:
        return f"<MrMatInfraException {self.code}: {self.msg}>"
