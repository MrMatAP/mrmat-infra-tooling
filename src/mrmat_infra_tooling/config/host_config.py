import pathlib

from pydantic import Field

from mrmat_infra_tooling import __default_keytab_path__
from mrmat_infra_tooling.config import RootConfigAware

class HostConfig(RootConfigAware):
    keytab: pathlib.Path = Field(description="Path to the Host keytab file",
                                 default=__default_keytab_path__)
    principal: str = Field(description="Host principal to use for authentication",
                           default="host/something@DOMAIN.ORG")
