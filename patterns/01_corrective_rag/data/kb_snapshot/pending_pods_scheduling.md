# Educational Test Fixture: Troubleshooting Pending Pods and Scheduling

## Overview
A Pod remains in `Pending` state when kube-scheduler cannot find an eligible cluster node that satisfies all resource requests, node selectors, taints, or volume bindings.

## Common Causes
1. **Insufficient Node CPU or Memory**: Requested resources exceed allocatable capacity across all schedulable nodes.
2. **Unmatched Taints and Tolerations**: Worker nodes have taints that the Pod specification does not tolerate.
3. **Unbound PersistentVolumeClaim (PVC)**: Pod references a PVC that is not bound to a PersistentVolume.
