# MrMat :: Infra Tooling

Tooling for integration in my ecosystem"

## mrmat-infra-config

Manage configuration for the infrastructural tooling.

```shell
$ /opt/homebrew/bin/uvx --from git+https://github.com/MrMatAP/mrmat-infra-tooling.git@1.1.4 mrmat-infra-config set dns.forward_zone mrmat.org
```

## mrmat-infra-dns-update

Registers this hosts FQDN both in forward and reverse zone using GSS-TSIG.

```shell
$ /opt/homebrew/bin/uvx --from git+https://github.com/MrMatAP/mrmat-infra-tooling.git@1.1.7 mrmat-infra-dns-update
Updated covenant with ['172.16.0.139', '2a02:1210:221b:a880:1c8b:a558:89ed:6738']
```
