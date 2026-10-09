# Atlas Proxmox VE plugin

Read-only Proxmox inventory for your homelab: nodes, virtual machines, LXC containers, storage and network interfaces. Independent Atlas repository add-in; no core application changes required.

## What it imports

| Proxmox object | Atlas representation |
| --- | --- |
| Node | Server with configured interfaces, bridges, bonds and addresses |
| QEMU guest | Virtual machine hosted on its node |
| LXC guest | LXC application with configured static addresses |
| Storage | Storage service hosted on its node |
| Guest disk on known storage | Uses storage relationship |

Guest IDs remain stable across migration. The connector reads configuration, not CPU/load metrics. It does not start, stop or modify guests, inspect guest secrets, run guest-agent commands or discover live guest IPs. Bridge names and VLAN declarations are documented as configured; no physical cable connection is invented. Offline nodes remain represented; configuration fields not retrievable are omitted instead of clearing previous values. An API failure aborts the whole import.

## Install in Atlas

1. Open **Sources & settings → Add-ins → Add GitHub repository**.
2. Enter `https://github.com/42bios/atlas-plugin-proxmox`.
3. Review the commit and files, then confirm trust with `42bios/atlas-plugin-proxmox`.
4. Create a connector instance with your HTTPS server URL, usually `https://pve.example:8006`, and a cluster display name.
5. Enter credential JSON privately, then save and select **Import now**. Start with manual imports before enabling a schedule.

Credential example (placeholder values only):

```json
{"tokenId":"atlas@pve!inventory","secret":"YOUR_TOKEN_SECRET","ca":"OPTIONAL_CLUSTER_CA_PEM"}
```

Use a dedicated Proxmox API token with read-only inventory permissions. `PVEAuditor` on the intended scope provides audit access; with privilege separation, both the user and token need applicable permissions. Limit the scope to the objects you intend to import. TLS verification stays enabled. For a private/self-signed CA, supply its PEM certificate in the credential JSON; do not disable verification. Credentials remain on the Atlas host and are never committed here.

## Compatibility and validation

Uses `/api2/json/cluster/resources`, node network configuration and QEMU/LXC guest configuration endpoints. Fixture tests cover relationships, migration identity, bonds, VLANs, address normalization, offline nodes, failures and secret exclusion. **Live Proxmox validation is pending** until a server URL and credential are configured; this is an initial 0.1.0 release.

## Development

Run `python -m unittest discover -s tests`. After editing declared files, run `python tools/update_manifest.py` and increment the manifest version for a release. CI validates package integrity and collector fixtures.

Repository code runs with Atlas application permissions. Download checksums identify files; they do not establish author trust or sandbox execution. Install only reviewed code.

API references: [Proxmox VE API documentation](https://pve.proxmox.com/wiki/Proxmox_VE_API), [API viewer](https://pve.proxmox.com/pve-docs/api-viewer/index.html), [cluster resource implementation](https://github.com/proxmox/pve-manager/blob/master/PVE/API2/Cluster.pm), [network API implementation](https://github.com/proxmox/pve-manager/blob/master/PVE/API2/Network.pm).
