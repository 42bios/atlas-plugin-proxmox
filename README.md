# Atlas Proxmox VE plugin

**Status: planned — not installable yet.** This repository reserves the independent Atlas connector project. It contains no collector or installable `atlas-addin.json`; Atlas will correctly reject installation until an implementation is released.

## Intended scope

Nodes, virtual machines, LXC containers, storage and network interfaces. Read-only inventory snapshots with stable IDs, preserving Atlas's manual documentation.

## Implementation milestones

1. Establish a read-only upstream API contract and representative fixtures.
2. Implement authenticated requests with TLS verification and bounded pagination/timeouts.
3. Normalize inventory to Atlas connector API 1 without exporting secrets.
4. Add fixture tests and validate with a real installation.
5. Publish the installable manifest and versioned release.

Credentials must remain private on the Atlas host. Do not put tokens, passwords or private infrastructure exports in GitHub issues.
