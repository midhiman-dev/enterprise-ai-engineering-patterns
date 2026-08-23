# Educational Test Fixture: Cluster Networking & CoreDNS Troubleshooting

## Overview
Cluster DNS failures prevent pods from resolving internal Service DNS names (e.g., `myservice.default.svc.cluster.local`) or external endpoints.

## Diagnostics
1. **CoreDNS Pod Status**: Verify CoreDNS pods are running in `kube-system` namespace.
2. **ClusterIP Service Connectivity**: Ensure kube-proxy IP virtual routing rules are active.
