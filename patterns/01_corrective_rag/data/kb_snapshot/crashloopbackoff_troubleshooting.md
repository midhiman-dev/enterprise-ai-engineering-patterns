# Educational Test Fixture: Kubernetes CrashLoopBackOff Troubleshooting

## Overview
`CrashLoopBackOff` indicates that a Kubernetes pod repeatedly starts, crashes, and attempts to restart. Kubernetes uses an exponential backoff delay for restarts to prevent resource exhaustion on cluster nodes.

## Common Causes
1. **Application Runtime Crash**: Uncaught exceptions, missing dependencies, or incompatible software versions causing the main application process to exit immediately with a non-zero exit code.
2. **Missing Configuration or Secrets**: The application relies on environment variables, ConfigMaps, or Secret volumes that are missing or misconfigured.
3. **Resource Limit Exhaustion (OOMKilled)**: The container exceeds its memory limit defined in the pod specification, causing the Linux OOM killer to terminate the process.
4. **Failed Liveness or Startup Probes**: The liveness probe repeatedly fails, causing kubelet to restart the container before it becomes healthy.

## Diagnostic Commands
* Inspect current container logs: `kubectl logs <pod-name>`
* Inspect previous failed container logs: `kubectl logs <pod-name> --previous`
* View detailed pod events and termination status: `kubectl describe pod <pod-name>`
