import importlib.metadata
import pathlib

try:
    __version__ = importlib.metadata.version('kube-eng')
except importlib.metadata.PackageNotFoundError:
    # You have not yet installed this as a package, likely because you're hacking on it in some IDE
    __version__ = '0.0.0.dev0'

__default_config_path__ = pathlib.Path('/opt/mrmat/etc/mrmat-infra-tooling.yaml')
__default_keytab_path__ = pathlib.Path('/opt/mrmat/etc/krb5.keytab')
