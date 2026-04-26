import argparse
import asyncio
import dataclasses
import ipaddress
import pathlib
import socket
import subprocess
import sys

import rich.console

from mrmat_infra_tooling import __version__, __default_config_path__
from mrmat_infra_tooling.config import RootConfig
from mrmat_infra_tooling.exceptions import MrMatInfraException

console = rich.console.Console()


@dataclasses.dataclass
class HostAddresses:
    ipv4: list[str] = dataclasses.field(default_factory=list)
    ipv6: list[str] = dataclasses.field(default_factory=list)


def get_secured_ipv6_addresses() -> list[str]:
    """Return IPv6 addresses with the 'autoconf secured' flag (RFC 7217 stable privacy)."""
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    addrs = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if 'inet6' in parts and 'autoconf' in parts and 'secured' in parts:
            addr = parts[parts.index('inet6') + 1].split('%')[0]
            try:
                parsed = ipaddress.ip_address(addr)
                if not parsed.is_link_local and not parsed.is_loopback:
                    addrs.append(addr)
            except ValueError:
                pass
    return addrs


def get_host_addresses(hostname: str) -> HostAddresses:
    """
    Discover current IPv4 and IPv6 addresses for this host.
    IPv4: all non-loopback, non-link-local addresses.
    IPv6: only 'autoconf secured' (stable privacy) addresses.
    """
    addrs = HostAddresses()
    info = socket.getaddrinfo(hostname, None)

    seen: set[str] = set()
    for item in info:
        _, _, _, _, sockaddr = item
        addr = sockaddr[0]
        if addr in seen:
            continue
        seen.add(addr)

        try:
            parsed = ipaddress.ip_address(addr)
        except ValueError:
            continue

        if parsed.is_loopback or parsed.is_link_local:
            continue

        if isinstance(parsed, ipaddress.IPv4Address):
            addrs.ipv4.append(addr)

    addrs.ipv6 = get_secured_ipv6_addresses()
    return addrs


def build_nsupdate_script(hostname: str, addrs: HostAddresses, server: str, ttl: int, forward_zone: str) -> str:
    """Build an nsupdate script for forward and reverse DNS updates."""
    zone = forward_zone if forward_zone.endswith('.') else forward_zone + '.'
    fqdn = hostname if hostname.endswith('.') else f'{hostname}.{zone}'
    lines = [f'server {server}']

    if addrs.ipv4:
        lines.append(f'update delete {fqdn} A')
        for ip in addrs.ipv4:
            lines.append(f'update add {fqdn} {ttl} A {ip}')
    if addrs.ipv6:
        lines.append(f'update delete {fqdn} AAAA')
        for ip in addrs.ipv6:
            lines.append(f'update add {fqdn} {ttl} AAAA {ip}')
    if addrs.ipv4 or addrs.ipv6:
        lines.append('send')

    for ip in addrs.ipv4 + addrs.ipv6:
        ptr = ptr_name(ip)
        lines.append(f'update delete {ptr} PTR')
        lines.append(f'update add {ptr} {ttl} PTR {fqdn}')
        lines.append('send')

    return '\n'.join(lines) + '\n'


def nsupdate(script: str, timeout: float = 30.0) -> None:
    """Run nsupdate -g with the given script on stdin."""
    try:
        result = subprocess.run(
            ['nsupdate', '-g'],
            input=script, capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        raise MrMatInfraException(code=500, msg='nsupdate not found')
    except subprocess.TimeoutExpired:
        raise MrMatInfraException(code=500, msg='nsupdate timed out')
    if result.returncode != 0:
        raise MrMatInfraException(code=500, msg=f'nsupdate failed: {result.stderr.strip()}')


def ptr_name(addr: str) -> str:
    """Return the PTR record name for an IP address."""
    parsed = ipaddress.ip_address(addr)
    if isinstance(parsed, ipaddress.IPv4Address):
        return '.'.join(reversed(addr.split('.'))) + '.in-addr.arpa.'
    else:
        expanded = parsed.exploded.replace(':', '')
        return '.'.join(reversed(expanded)) + '.ip6.arpa.'


def kinit(keytab: pathlib.Path, principal: str, timeout: float = 15.0) -> None:
    """Obtain a Kerberos TGT from the given keytab."""
    try:
        result = subprocess.run(
            ["kinit", "-k", "-t", str(keytab), principal],
            capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        raise MrMatInfraException(code=500, msg="kinit not found")
    except subprocess.TimeoutExpired:
        raise MrMatInfraException(code=500, msg="kinit timed out")
    if result.returncode != 0:
        raise MrMatInfraException(code=500, msg=f"kinit failed: {result.stderr.strip()}")


async def main() -> int:
    try:
        parser = argparse.ArgumentParser(f'mrmat-infra-dns-update {__version__}')
        parser.add_argument(
            '--config',
            type=pathlib.Path,
            required=False,
            dest='config_path',
            default=__default_config_path__,
            help=f'Path to the config file, defaults to {__default_config_path__}',
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            default=False,
            dest='verbose',
            help='Enable verbose output',
        )
        args = parser.parse_args()
        config = RootConfig.load(config_path=args.config_path)

        hostname = socket.gethostname().removesuffix('.local')
        if hostname.endswith(config.dns.forward_zone):
            hostname = hostname.split('.')[0]
        addrs = get_host_addresses(hostname)
        kinit(keytab=config.host.keytab, principal=config.host.principal)
        script = build_nsupdate_script(
            hostname=hostname,
            forward_zone=config.dns.forward_zone,
            addrs=addrs,
            server=config.dns.primary,
            ttl=config.dns.ttl,
        )
        if args.verbose:
            console.print(script)
        nsupdate(script)
        console.print(f'Updated {hostname} with {addrs.ipv4 + addrs.ipv6}')
        return 0
    except KeyboardInterrupt:
        return 0
    except MrMatInfraException as e:
        console.print(e)
    except Exception as e:
        console.print(e)
    return 1


def run() -> int:
    return asyncio.run(main())


if __name__ == '__main__':
    sys.exit(run())
