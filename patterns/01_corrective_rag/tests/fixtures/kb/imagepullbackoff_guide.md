# Educational Test Fixture: ImagePullBackOff & ErrImagePull Guide

## Overview
`ImagePullBackOff` occurs when Kubernetes kubelet fails to retrieve the specified container image from a container registry. Like CrashLoopBackOff, kubelet waits before retrying with an exponential backoff.

## Common Causes
1. **Incorrect Image Tag or Name**: Typos in container image repository path or tag.
2. **Private Registry Authentication Failure**: Missing or invalid `imagePullSecrets` in pod specification.
3. **Network Failure or Registry Outage**: Node cannot reach container registry due to network restrictions or registry downtime.
