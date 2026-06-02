#!/usr/bin/env python3
"""
AIOps Incident Correlation & Auto-Remediation Engine

This script demonstrates:
1. Querying Prometheus for metrics anomalies
2. Correlating with pod logs
3. Using pattern matching (pseudo-AI) to determine root cause
4. Executing auto-remediation (HPA scaling, pod restart, etc.)
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AnomalyIndicator:
    """Represents a detected anomaly in metrics or logs."""
    metric_name: str
    value: float
    threshold: float
    severity: str  # "critical", "high", "medium", "low"
    detected_at: datetime
    detail: str


@dataclass
class RootCauseAnalysis:
    """Result of root cause analysis."""
    primary_cause: str
    confidence: float  # 0.0 to 1.0
    contributing_factors: List[str]
    recommended_actions: List[str]
    explanation: str


class PrometheusQueryClient:
    """Client for querying Prometheus metrics."""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """Initialize Prometheus client."""
        self.base_url = prometheus_url
        self.session = requests.Session()
    
    def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "15s"
    ) -> Optional[List[Dict]]:
        """
        Execute a Prometheus range query.
        
        Args:
            query: PromQL query
            start: Start time
            end: End time
            step: Query resolution step
            
        Returns:
            Query results or None if error
        """
        try:
            url = urljoin(self.base_url, "/api/v1/query_range")
            params = {
                "query": query,
                "start": int(start.timestamp()),
                "end": int(end.timestamp()),
                "step": step
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") != "success":
                logger.error(f"Prometheus error: {data.get('error', 'Unknown')}")
                return None
            
            return data.get("data", {}).get("result", [])
            
        except requests.RequestException as e:
            logger.error(f"Failed to query Prometheus: {e}")
            return None
    
    def query_instant(self, query: str) -> Optional[List[Dict]]:
        """Execute a Prometheus instant query."""
        try:
            url = urljoin(self.base_url, "/api/v1/query")
            params = {"query": query}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") != "success":
                logger.error(f"Prometheus error: {data.get('error', 'Unknown')}")
                return None
            
            return data.get("data", {}).get("result", [])
            
        except requests.RequestException as e:
            logger.error(f"Failed to query Prometheus: {e}")
            return None


class IncidentDetector:
    """Detects anomalies in metrics and logs."""
    
    def __init__(self, prometheus_client: PrometheusQueryClient):
        """Initialize incident detector."""
        self.prometheus = prometheus_client
    
    def detect_pod_memory_anomaly(
        self,
        namespace: str,
        pod_label: str,
        minutes: int = 5
    ) -> Optional[AnomalyIndicator]:
        """Detect abnormal memory usage."""
        query = (
            f'container_memory_usage_bytes{{'
            f'namespace="{namespace}",pod=~".*{pod_label}.*"}}'
        )
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        results = self.prometheus.query_range(query, start_time, end_time)
        if not results:
            return None
        
        # Check for spike in latest data
        latest_value = float(results[0]["values"][-1][1]) if results[0]["values"] else 0
        
        # Threshold: 500MB
        threshold = 500 * 1024 * 1024
        
        if latest_value > threshold:
            return AnomalyIndicator(
                metric_name="container_memory_usage_bytes",
                value=latest_value,
                threshold=threshold,
                severity="high",
                detected_at=datetime.utcnow(),
                detail=f"Memory usage: {latest_value / (1024*1024):.1f}MB"
            )
        
        return None
    
    def detect_pod_cpu_spike(
        self,
        namespace: str,
        pod_label: str,
        minutes: int = 5
    ) -> Optional[AnomalyIndicator]:
        """Detect abnormal CPU usage."""
        query = (
            f'rate(container_cpu_usage_seconds_total{{'
            f'namespace="{namespace}",pod=~".*{pod_label}.*"}}[1m])'
        )
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        results = self.prometheus.query_range(query, start_time, end_time)
        if not results:
            return None
        
        latest_value = float(results[0]["values"][-1][1]) if results[0]["values"] else 0
        
        # Threshold: 1.5 cores (1500m)
        threshold = 1.5
        
        if latest_value > threshold:
            return AnomalyIndicator(
                metric_name="container_cpu_usage",
                value=latest_value,
                threshold=threshold,
                severity="high",
                detected_at=datetime.utcnow(),
                detail=f"CPU usage: {latest_value * 1000:.0f}m"
            )
        
        return None
    
    def detect_pod_restart_loop(
        self,
        namespace: str,
        pod_label: str
    ) -> Optional[AnomalyIndicator]:
        """Detect pods in restart loop."""
        query = (
            f'kube_pod_container_status_restarts_total{{'
            f'namespace="{namespace}",pod=~".*{pod_label}.*"}}'
        )
        
        results = self.prometheus.query_instant(query)
        if not results:
            return None
        
        restart_count = float(results[0]["value"][1]) if results else 0
        
        # Alert if > 3 restarts in short time
        if restart_count > 3:
            return AnomalyIndicator(
                metric_name="kube_pod_container_status_restarts_total",
                value=restart_count,
                threshold=3,
                severity="critical",
                detected_at=datetime.utcnow(),
                detail=f"Pod restart count: {int(restart_count)}"
            )
        
        return None
    
    def detect_readiness_probe_failure(
        self,
        namespace: str,
        pod_label: str
    ) -> Optional[AnomalyIndicator]:
        """Detect readiness probe failures."""
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "pods", "-n", namespace,
                    "-l", f"app={pod_label}",
                    "-o", "json"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            pods = json.loads(result.stdout).get("items", [])
            
            for pod in pods:
                conditions = pod.get("status", {}).get("conditions", [])
                for condition in conditions:
                    if (condition.get("type") == "Ready" and
                        condition.get("status") != "True"):
                        return AnomalyIndicator(
                            metric_name="pod_ready_status",
                            value=0,
                            threshold=1,
                            severity="high",
                            detected_at=datetime.utcnow(),
                            detail=f"Pod {pod['metadata']['name']} not ready"
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting readiness probe failure: {e}")
            return None


class LogCorrelator:
    """Correlates logs with detected anomalies."""
    
    LOG_PATTERNS = {
        "out_of_memory": {
            "regex": r"(out of memory|OOMKilled|Killed|Memory limit|MemoryError)",
            "severity": "critical",
            "category": "Resource Exhaustion"
        },
        "connection_refused": {
            "regex": r"(Connection refused|ECONNREFUSED|cannot connect)",
            "severity": "high",
            "category": "Connectivity"
        },
        "database_error": {
            "regex": r"(connection timeout|database error|SQL error|query timeout)",
            "severity": "high",
            "category": "Database"
        },
        "permission_denied": {
            "regex": r"(Permission denied|EACCES|Access denied|Forbidden)",
            "severity": "high",
            "category": "Security"
        },
        "timeout": {
            "regex": r"(timeout|timed out|Timeout|ETIMEDOUT)",
            "severity": "medium",
            "category": "Timeout"
        },
        "disk_full": {
            "regex": r"(disk full|No space left|ENOSPC)",
            "severity": "high",
            "category": "Disk"
        },
        "high_load": {
            "regex": r"(load average|too busy|high CPU)",
            "severity": "medium",
            "category": "Load"
        }
    }
    
    def correlate_logs_with_anomaly(
        self,
        namespace: str,
        pod_label: str,
        anomaly: AnomalyIndicator,
        tail_lines: int = 50
    ) -> Dict[str, any]:
        """
        Correlate pod logs with detected anomaly.
        
        Returns:
            Dictionary with matched patterns and details
        """
        try:
            # Get pod logs
            result = subprocess.run(
                [
                    "kubectl", "logs",
                    "-n", namespace,
                    "-l", f"app={pod_label}",
                    "--tail", str(tail_lines),
                    "--timestamps=true"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Could not retrieve logs: {result.stderr}")
                return {}
            
            logs = result.stdout
            
            # Search for patterns
            matched_patterns = {}
            
            for pattern_name, pattern_info in self.LOG_PATTERNS.items():
                regex = pattern_info["regex"]
                matches = re.findall(regex, logs, re.IGNORECASE)
                
                if matches:
                    matched_patterns[pattern_name] = {
                        "count": len(matches),
                        "category": pattern_info["category"],
                        "severity": pattern_info["severity"],
                        "examples": list(set(matches))[:3]  # Top 3 unique matches
                    }
            
            return {
                "log_entries_analyzed": len(logs.split('\n')),
                "patterns_matched": matched_patterns,
                "log_snippet": logs[:500]  # First 500 chars
            }
            
        except Exception as e:
            logger.error(f"Error correlating logs: {e}")
            return {}


class RootCauseAnalyzer:
    """Analyzes root causes of incidents using pattern matching."""
    
    def analyze(
        self,
        anomalies: List[AnomalyIndicator],
        log_correlation: Dict
    ) -> RootCauseAnalysis:
        """
        Analyze root cause based on anomalies and logs.
        
        Uses heuristic-based analysis (simulating AI without ML models).
        """
        
        primary_cause = "Unknown"
        confidence = 0.0
        contributing_factors = []
        recommended_actions = []
        explanation = ""
        
        # Analyze anomalies
        anomaly_types = [a.metric_name for a in anomalies]
        patterns = log_correlation.get("patterns_matched", {})
        
        # Memory issue
        if any("memory" in a for a in anomaly_types) and "out_of_memory" in patterns:
            primary_cause = "Memory Exhaustion (OOM Killer)"
            confidence = 0.95
            explanation = (
                "Pod exceeded memory limit, triggering OOM killer. "
                "Kubernetes automatically terminated the container."
            )
            recommended_actions = [
                "Scale up pod resources: increase memory limit in deployment",
                "Analyze code for memory leaks in startup sequence",
                "Enable HPA to auto-scale based on memory pressure",
                "Review application logs for memory-hungry operations"
            ]
        
        # CPU spike
        elif any("cpu" in a for a in anomaly_types) and "high_load" in patterns:
            primary_cause = "CPU Overload"
            confidence = 0.85
            explanation = (
                "Pod CPU usage exceeded expected levels. "
                "This indicates either heavy processing load or infinite loops."
            )
            recommended_actions = [
                "Enable HPA CPU autoscaling (target 70% utilization)",
                "Investigate recent code changes for performance regressions",
                "Check for N+1 query patterns in database access",
                "Profile application with CPU profiler"
            ]
        
        # Readiness probe failure
        elif "pod_ready_status" in [a.metric_name for a in anomalies]:
            if "database_error" in patterns:
                primary_cause = "Database Connection Failure"
                confidence = 0.90
                explanation = (
                    "Pod readiness probe failing because database is unreachable. "
                    "Likely causes: DB service down, network partition, or credentials."
                )
                recommended_actions = [
                    "Check database service status: kubectl get svc -n <db-namespace>",
                    "Verify database credentials in pod environment",
                    "Check network policies allowing pod-to-database communication",
                    "Verify database is accepting connections (test with psql/mysql CLI)"
                ]
            elif "connection_refused" in patterns:
                primary_cause = "Service Unavailable"
                confidence = 0.80
                explanation = (
                    "Pod readiness probe failing due to service connectivity issues. "
                    "The pod or a dependency is not ready to accept traffic."
                )
                recommended_actions = [
                    "Check dependent service status: kubectl describe deployment",
                    "Increase readiness probe initial delay and timeout",
                    "Verify all init containers completed successfully",
                    "Check startup logs for service bootstrap failures"
                ]
            else:
                primary_cause = "Readiness Probe Failure"
                confidence = 0.70
                explanation = (
                    "Pod failed its readiness check. "
                    "This prevents traffic routing but doesn't auto-kill the pod."
                )
                recommended_actions = [
                    "Check pod logs for startup errors: kubectl logs <pod>",
                    "Verify probe endpoint is actually implementing /ready",
                    "Increase probe timeout if it's a slow startup",
                    "Check if readiness probe is misconfigured"
                ]
        
        # Restart loop
        elif any("restarts_total" in a for a in anomaly_types):
            primary_cause = "Crash Loop (CrashLoopBackOff)"
            confidence = 0.92
            explanation = (
                "Pod is repeatedly crashing and restarting. "
                "Usually indicates a bug introduced in recent code change."
            )
            recommended_actions = [
                "Check recent deployments: kubectl rollout history deployment/<name>",
                "Rollback to previous stable version if crash is new",
                "Review pod logs for stack traces: kubectl logs <pod> --previous",
                "Check container startup command and arguments",
                "Increase restart policy delay to prevent rapid restarts"
            ]
        
        # Default: disk or timeout issue
        elif "disk_full" in patterns:
            primary_cause = "Disk Space Exhaustion"
            confidence = 0.88
            explanation = (
                "Pod hitting disk space limits. "
                "Likely causes: excessive logging, temp files, or PVC too small."
            )
            recommended_actions = [
                "Check disk usage: kubectl exec <pod> -- df -h",
                "Clean up temporary files and logs",
                "Increase PVC size if applicable",
                "Enable log rotation for application logs",
                "Check for runaway processes creating files"
            ]
        elif "timeout" in patterns:
            primary_cause = "Timeout Communicating with Dependencies"
            confidence = 0.75
            explanation = (
                "Pod operations timing out when connecting to external services. "
                "Indicates network latency or service performance issues."
            )
            recommended_actions = [
                "Increase timeout values in pod configuration",
                "Check network latency: kubectl exec <pod> -- ping <service>",
                "Verify service endpoints are actually running",
                "Check for network policies blocking traffic",
                "Monitor external service performance metrics"
            ]
        else:
            # Generic analysis based on patterns
            if patterns:
                pattern_categories = set(
                    p.get("category") for p in patterns.values()
                )
                primary_cause = f"Multiple Issues: {', '.join(pattern_categories)}"
                confidence = 0.60
                explanation = (
                    "Multiple issues detected in logs but no single dominant cause. "
                    "Recommend manual investigation and log review."
                )
                recommended_actions = [
                    "Review full pod logs: kubectl logs <pod> -f",
                    "Check pod events: kubectl describe pod <pod>",
                    "Examine metrics dashboard for correlation",
                    "Contact platform team for expert analysis"
                ]
        
        # Add contributing factors
        if anomalies:
            contributing_factors = [
                f"{a.metric_name}: {a.detail}"
                for a in anomalies
            ]
        
        if patterns:
            contributing_factors.extend([
                f"Log pattern: {name} (severity: {info['severity']})"
                for name, info in patterns.items()
            ])
        
        return RootCauseAnalysis(
            primary_cause=primary_cause,
            confidence=confidence,
            contributing_factors=contributing_factors,
            recommended_actions=recommended_actions,
            explanation=explanation
        )


class AutoRemediator:
    """Executes automatic remediation actions."""
    
    def trigger_hpa_scale(
        self,
        deployment: str,
        namespace: str,
        min_replicas: int = 2,
        max_replicas: int = 10,
        target_cpu: int = 70
    ) -> bool:
        """
        Create or update HPA for a deployment.
        
        Args:
            deployment: Deployment name
            namespace: Kubernetes namespace
            min_replicas: Minimum replicas
            max_replicas: Maximum replicas
            target_cpu: Target CPU utilization percentage
            
        Returns:
            True if successful
        """
        try:
            # Check if HPA already exists
            result = subprocess.run(
                ["kubectl", "get", "hpa", deployment, "-n", namespace],
                capture_output=True,
                timeout=10
            )
            
            hpa_exists = result.returncode == 0
            
            # Create HPA manifest
            hpa_manifest = f"""
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {deployment}
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {deployment}
  minReplicas: {min_replicas}
  maxReplicas: {max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {target_cpu}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""
            
            # Apply manifest
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=hpa_manifest,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                action = "Updated" if hpa_exists else "Created"
                logger.info(f"{action} HPA for {deployment}")
                return True
            else:
                logger.error(f"Failed to apply HPA: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering HPA scale: {e}")
            return False
    
    def restart_pod(
        self,
        namespace: str,
        pod_label: str
    ) -> bool:
        """
        Restart pod by triggering a rollout restart.
        
        Args:
            namespace: Kubernetes namespace
            pod_label: Pod label selector
            
        Returns:
            True if successful
        """
        try:
            # Get deployment name from pod label
            result = subprocess.run(
                [
                    "kubectl", "get", "deployment", "-n", namespace,
                    "-l", f"app={pod_label}",
                    "-o", "jsonpath={.items[0].metadata.name}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0 or not result.stdout:
                logger.error("Could not find deployment")
                return False
            
            deployment = result.stdout.strip()
            
            # Restart deployment
            result = subprocess.run(
                [
                    "kubectl", "rollout", "restart",
                    f"deployment/{deployment}",
                    "-n", namespace
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Restarted deployment {deployment}")
                return True
            else:
                logger.error(f"Failed to restart deployment: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restarting pod: {e}")
            return False
    
    def scale_deployment(
        self,
        deployment: str,
        namespace: str,
        replicas: int
    ) -> bool:
        """
        Manually scale a deployment.
        
        Args:
            deployment: Deployment name
            namespace: Kubernetes namespace
            replicas: Number of replicas
            
        Returns:
            True if successful
        """
        try:
            result = subprocess.run(
                [
                    "kubectl", "scale", "deployment", deployment,
                    "--replicas", str(replicas),
                    "-n", namespace
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Scaled {deployment} to {replicas} replicas")
                return True
            else:
                logger.error(f"Failed to scale deployment: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error scaling deployment: {e}")
            return False


def print_analysis_report(
    anomalies: List[AnomalyIndicator],
    log_correlation: Dict,
    root_cause: RootCauseAnalysis
):
    """Print formatted incident analysis report."""
    
    print("\n" + "="*70)
    print("  INCIDENT ANALYSIS REPORT")
    print("="*70)
    
    # Anomalies
    print("\n📊 DETECTED ANOMALIES:")
    print("-" * 70)
    if anomalies:
        for anomaly in anomalies:
            print(f"  • {anomaly.metric_name}")
            print(f"    Value: {anomaly.value:.2f} (Threshold: {anomaly.threshold:.2f})")
            print(f"    Severity: {anomaly.severity.upper()}")
            print(f"    Detail: {anomaly.detail}")
    else:
        print("  No anomalies detected")
    
    # Log Correlation
    print("\n📝 LOG CORRELATION:")
    print("-" * 70)
    if log_correlation:
        log_entries = log_correlation.get("log_entries_analyzed", 0)
        print(f"  Log entries analyzed: {log_entries}")
        
        patterns = log_correlation.get("patterns_matched", {})
        if patterns:
            print(f"  Patterns matched: {len(patterns)}")
            for pattern_name, pattern_info in patterns.items():
                print(f"    • {pattern_name} ({pattern_info['category']})")
                print(f"      Severity: {pattern_info['severity']}")
                print(f"      Count: {pattern_info['count']}")
        else:
            print("  No error patterns matched")
    else:
        print("  Could not retrieve logs")
    
    # Root Cause Analysis
    print("\n🔍 ROOT CAUSE ANALYSIS:")
    print("-" * 70)
    print(f"  Primary Cause: {root_cause.primary_cause}")
    print(f"  Confidence: {root_cause.confidence * 100:.0f}%")
    print(f"\n  Explanation:")
    for line in root_cause.explanation.split('\n'):
        print(f"    {line}")
    
    if root_cause.contributing_factors:
        print(f"\n  Contributing Factors:")
        for factor in root_cause.contributing_factors:
            print(f"    • {factor}")
    
    # Recommended Actions
    print("\n✅ RECOMMENDED ACTIONS:")
    print("-" * 70)
    for i, action in enumerate(root_cause.recommended_actions, 1):
        print(f"  {i}. {action}")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description="AIOps Incident Correlation & Remediation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze incident in default namespace
  %(prog)s --namespace default --pod-label todos-demo
  
  # Analyze and auto-remediate with HPA scaling
  %(prog)s --namespace default --pod-label todos-demo --auto-scale
  
  # Analyze and restart pod
  %(prog)s --namespace default --pod-label todos-demo --restart
  
  # Use custom Prometheus URL
  %(prog)s --prometheus http://prometheus.monitoring:9090 --namespace default
        """
    )
    
    parser.add_argument(
        "--namespace", "-n",
        default="default",
        help="Kubernetes namespace (default: default)"
    )
    
    parser.add_argument(
        "--pod-label", "-l",
        default="todos-demo",
        help="Pod label selector (default: todos-demo)"
    )
    
    parser.add_argument(
        "--prometheus",
        default="http://localhost:9090",
        help="Prometheus URL (default: http://localhost:9090)"
    )
    
    parser.add_argument(
        "--auto-scale",
        action="store_true",
        help="Enable HPA autoscaling as remediation"
    )
    
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart pods as remediation"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("Starting AIOps Incident Analysis")
    logger.info(f"Namespace: {args.namespace}, Pod Label: {args.pod_label}")
    logger.info(f"Prometheus: {args.prometheus}")
    
    # Initialize components
    prometheus = PrometheusQueryClient(args.prometheus)
    detector = IncidentDetector(prometheus)
    correlator = LogCorrelator()
    analyzer = RootCauseAnalyzer()
    remediator = AutoRemediator()
    
    # Detect anomalies
    logger.info("Scanning for anomalies...")
    anomalies = []
    
    memory_anomaly = detector.detect_pod_memory_anomaly(
        args.namespace, args.pod_label
    )
    if memory_anomaly:
        anomalies.append(memory_anomaly)
    
    cpu_anomaly = detector.detect_pod_cpu_spike(
        args.namespace, args.pod_label
    )
    if cpu_anomaly:
        anomalies.append(cpu_anomaly)
    
    restart_anomaly = detector.detect_pod_restart_loop(
        args.namespace, args.pod_label
    )
    if restart_anomaly:
        anomalies.append(restart_anomaly)
    
    readiness_anomaly = detector.detect_readiness_probe_failure(
        args.namespace, args.pod_label
    )
    if readiness_anomaly:
        anomalies.append(readiness_anomaly)
    
    if not anomalies:
        logger.info("No anomalies detected")
    else:
        logger.info(f"Detected {len(anomalies)} anomalies")
    
    # Correlate with logs
    logger.info("Correlating with application logs...")
    log_correlation = correlator.correlate_logs_with_anomaly(
        args.namespace, args.pod_label,
        anomalies[0] if anomalies else None
    )
    
    # Analyze root cause
    logger.info("Analyzing root cause...")
    root_cause = analyzer.analyze(anomalies, log_correlation)
    
    # Print report
    print_analysis_report(anomalies, log_correlation, root_cause)
    
    # Execute remediation if requested
    if args.auto_scale or args.restart:
        logger.info("Executing remediation actions...")
        
        if args.auto_scale:
            # Get deployment name
            result = subprocess.run(
                [
                    "kubectl", "get", "deployment", "-n", args.namespace,
                    "-l", f"app={args.pod_label}",
                    "-o", "jsonpath={.items[0].metadata.name}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                deployment = result.stdout.strip()
                logger.info(f"Enabling HPA for deployment {deployment}...")
                remediator.trigger_hpa_scale(deployment, args.namespace)
        
        if args.restart:
            logger.info(f"Restarting pods matching {args.pod_label}...")
            remediator.restart_pod(args.namespace, args.pod_label)


if __name__ == "__main__":
    main()
