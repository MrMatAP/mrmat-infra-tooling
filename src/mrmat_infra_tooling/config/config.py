import pathlib
from typing import Any

import yaml

from pydantic import BaseModel, Field, computed_field

from mrmat_infra_tooling import __version__, __default_config_path__
from mrmat_infra_tooling.config import RootConfigAware
from .host_config import HostConfig
from .dns_config import DNSConfig


class RootConfig(BaseModel):
    """
    Configuration of the kube-eng cluster
    """
    config_path: pathlib.Path = Field(description='Path to the configuration directory',
                                      default=__default_config_path__)

    host: HostConfig = Field(default_factory=HostConfig, description="Host configuration")
    dns: DNSConfig = Field(default_factory=DNSConfig, description="DNS configuration")

    @computed_field
    @property
    def version(self) -> str:
        """
        The current version of kube-eng

        Returns:
            The current version of kube-eng
        """
        return __version__

    @computed_field
    @property
    def config_file_path(self) -> pathlib.Path:
        """
        The actual configuration file within the config directory
        Returns:
            Path to the cluster configuration file
        """
        return self.config_path

    def save(self) -> None:
        """
        Save the current in-memory configuration to disk.
        Returns:
            Nothing
        """
        yaml.dump(self.model_dump(mode="json"), self.config_file_path.open("w"))

    @classmethod
    def load(cls, config_path: pathlib.Path = __default_config_path__) -> "RootConfig":
        """
        Load the configuration from disk.
        Args:
            config_path (Path): Path to the configuration directory.

        Returns:
            An initialised Config object.
        """
        if config_path.exists():
            return cls.model_validate(yaml.safe_load(config_path.open()))
        else:
            c = cls()
            c.config_path = config_path
            return c

    def model_post_init(self, context: Any, /) -> None:
        """
        Propagate a reference to this root configuration instance down the
        hierarchy. Pydantic invokes this method to let us know that the
        instance is fully initialised.

        Massaging of initial, unset defaults within the hierarchy must occur
        here because individual model_post_init methods within the hierarchy
        execute before this sets a reference to the root config.

        Args:
            context (): Undocumented parameter, appears to always be None
        """
        super().model_post_init(context)
        for field in dict(self).values():
            if issubclass(type(field), RootConfigAware):
                field.propagate_root_config(self)
