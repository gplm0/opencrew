# HEALTH - System Diagnostics and Optimization

## Overview
The HEALTH skill provides a systematic approach to diagnosing system issues, monitoring health metrics, and identifying optimization opportunities. It covers infrastructure, applications, and databases.

## Workflow

### 1. Symptom Assessment
- Clearly describe the observed problem: what, when, where, how often
- Identify the impact: which users, features, or services are affected?
- Determine urgency and severity
- Establish a baseline: what does "normal" look like for this system?
- Check if the issue is ongoing or intermittent

### 2. Metrics Collection
- Gather system metrics: CPU, memory, disk I/O, network usage
- Collect application metrics: response times, error rates, throughput, queue depth
- Review database metrics: query times, connection pool usage, lock contention
- Check infrastructure health: disk space, available memory, network latency
- Examine logs for errors, warnings, and unusual patterns
- Compare current metrics against historical baselines

### 3. Root Cause Analysis
- Start from the symptom and work backward through the dependency chain
- Use the 5 Whys technique: ask "why" iteratively to reach the root cause
- Correlate metrics: do spikes in one metric correspond with changes in another?
- Check recent changes: deployments, configuration updates, data migrations
- Isolate the problem: can you reproduce it in a controlled environment?
- Rule out external factors: third-party services, network issues, upstream dependencies

### 4. Performance Analysis
- Identify the bottleneck using profiling and tracing tools
- Determine if the issue is CPU-bound, memory-bound, I/O-bound, or network-bound
- Analyze the critical path: which operations dominate response time?
- Check for resource leaks: unclosed connections, memory leaks, file descriptor exhaustion
- Review database query plans: full table scans, missing indexes, inefficient joins
- Evaluate cache effectiveness: hit rates, eviction patterns, stale data

### 5. Optimization Planning
- Prioritize optimizations by impact: biggest performance gain for least effort
- Apply Amdahl's Law: optimizing a small part of the system has limited overall benefit
- Plan changes incrementally: measure, change, measure again
- Consider horizontal vs. vertical scaling options
- Evaluate architectural changes vs. tactical optimizations
- Document the expected improvement and how it will be measured

### 6. Implementation and Verification
- Implement changes one at a time; measure impact after each change
- Use feature flags or canary deployments for risky optimizations
- Monitor for regressions after changes are deployed
- Verify the fix addresses the root cause, not just the symptom
- Document the issue, diagnosis, fix, and metrics for future reference
- Set up alerts to detect recurrence

## Best Practices
- Measure before optimizing; never guess about performance
- Establish baselines and monitoring before problems occur
- Use structured logging with consistent levels (DEBUG, INFO, WARN, ERROR)
- Set up dashboards for key health metrics; review them regularly
- Automate health checks and alerting for critical services
- Keep a runbook for common issues: symptoms, diagnosis steps, fixes
- Capacity plan proactively: monitor growth trends and plan before hitting limits

## Diagnostic Commands and Tools
- **System**: top, htop, vmstat, iostat, netstat, df, free
- **Application**: profilers, APM tools (New Relic, Datadog), flame graphs
- **Database**: EXPLAIN ANALYZE, slow query log, connection stats
- **Network**: ping, traceroute, tcpdump, curl with timing
- **Logs**: grep for errors, tail for real-time, structured log queries

## Health Report Template
1. Symptom summary and impact assessment
2. Metrics collected with before/after comparison
3. Root cause identified with evidence
4. Fix applied and verification results
5. Recommendations for preventing recurrence
6. Follow-up actions and monitoring improvements
