from pydantic import Field

from mrmat_infra_tooling.config import RootConfigAware


class DNSConfig(RootConfigAware):
    primary: str = Field(description="Primary DNS server to use for DNS updates",
                         default="server.domain")
    ttl: int = Field(description="Default TTL for DNS records",
                     default=1800)
    forward_zone: str = Field(description="Forward DNS zone to use for updates",
                              default="domain.")
    reverse_zones: list[str] = Field(description="List of reverse DNS zones to use for updates",
                                     default=["1.168.192.in-addr.arpa.", "8.b.d.0.1.0.0.2.ip6.arpa."])
