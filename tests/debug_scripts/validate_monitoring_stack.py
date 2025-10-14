#!/usr/bin/env python3
"""
WhisperEngine Real-Time Monitoring Validation
============================================

Comprehensive validation of InfluxDB metrics collection and Grafana dashboard integration
for character intelligence performance monitoring.
"""

import asyncio
import json
import aiohttp
import requests
from typing import Dict, List, Any
from datetime import datetime
import sys
import os

class MonitoringStackValidator:
    """Validates WhisperEngine InfluxDB + Grafana monitoring stack"""
    
    def __init__(self):
        self.influxdb_url = "http://localhost:8087"
        self.grafana_url = "http://localhost:3002"
        self.elena_bot_url = "http://localhost:9091"
        self.gabriel_bot_url = "http://localhost:9095"
        self.sophia_bot_url = "http://localhost:9096"
        
        # Load monitoring credentials
        self.load_monitoring_config()
        
        self.test_results = []
        
    def load_monitoring_config(self):
        """Load monitoring configuration from .env.monitoring"""
        config_file = ".env.monitoring"
        self.influxdb_token = "whisperengine_admin_token"
        self.grafana_user = "admin"
        self.grafana_password = "admin"
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key == "INFLUXDB_TOKEN":
                            self.influxdb_token = value
                        elif key == "GRAFANA_USER":
                            self.grafana_user = value
                        elif key == "GRAFANA_PASSWORD":
                            self.grafana_password = value
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    async def test_influxdb_health(self) -> bool:
        """Test InfluxDB health and connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.influxdb_url}/ping") as response:
                    if response.status == 204:
                        self.log_test("InfluxDB Health Check", "PASS", "InfluxDB is responsive")
                        return True
                    else:
                        self.log_test("InfluxDB Health Check", "FAIL", f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("InfluxDB Health Check", "FAIL", f"Connection error: {e}")
            return False
    
    async def test_grafana_health(self) -> bool:
        """Test Grafana health and API availability"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.grafana_url}/api/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        self.log_test("Grafana Health Check", "PASS", f"Version: {health_data.get('version', 'unknown')}")
                        return True
                    else:
                        self.log_test("Grafana Health Check", "FAIL", f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Grafana Health Check", "FAIL", f"Connection error: {e}")
            return False
    
    async def test_character_bot_health(self) -> Dict[str, bool]:
        """Test character bot health endpoints"""
        bots = {
            "elena": self.elena_bot_url,
            "gabriel": self.gabriel_bot_url,
            "sophia": self.sophia_bot_url
        }
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for bot_name, bot_url in bots.items():
                try:
                    async with session.get(f"{bot_url}/health") as response:
                        if response.status == 200:
                            health_data = await response.json()
                            self.log_test(f"{bot_name.title()} Bot Health", "PASS", 
                                        f"Status: {health_data.get('status', 'unknown')}")
                            results[bot_name] = True
                        else:
                            self.log_test(f"{bot_name.title()} Bot Health", "FAIL", f"HTTP {response.status}")
                            results[bot_name] = False
                except Exception as e:
                    self.log_test(f"{bot_name.title()} Bot Health", "FAIL", f"Connection error: {e}")
                    results[bot_name] = False
        
        return results
    
    async def test_metrics_collection(self) -> bool:
        """Test real-time metrics collection by triggering bot conversations"""
        try:
            # Test message to Elena bot to trigger metrics collection
            test_message = {
                "user_id": "monitoring_test_user",
                "message": "Hello Elena! How are you feeling today?",
                "context": {
                    "channel_type": "api",
                    "platform": "monitoring_test",
                    "metadata": {}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                # Send test message to Elena bot
                async with session.post(f"{self.elena_bot_url}/api/chat", 
                                      json=test_message) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # Check if metrics are present in response
                        processing_time = response_data.get('processing_time_ms', 0)
                        if processing_time > 0:
                            self.log_test("Metrics Collection Test", "PASS", 
                                        f"Processing time recorded: {processing_time}ms")
                            return True
                        else:
                            self.log_test("Metrics Collection Test", "WARN", 
                                        "Response received but no processing time recorded")
                            return False
                    else:
                        self.log_test("Metrics Collection Test", "FAIL", f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.log_test("Metrics Collection Test", "FAIL", f"Error: {e}")
            return False
    
    def test_grafana_dashboards(self) -> bool:
        """Test Grafana dashboard availability"""
        try:
            # List all dashboards
            response = requests.get(
                f"{self.grafana_url}/api/search?type=dash-db",
                auth=(self.grafana_user, self.grafana_password),
                timeout=10
            )
            
            if response.status_code == 200:
                dashboards = response.json()
                whisperengine_dashboards = [d for d in dashboards if 'whisperengine' in d.get('title', '').lower()]
                
                if len(whisperengine_dashboards) >= 3:  # Expect at least 3 main dashboards
                    dashboard_titles = [d['title'] for d in whisperengine_dashboards]
                    self.log_test("Grafana Dashboards", "PASS", 
                                f"Found {len(whisperengine_dashboards)} WhisperEngine dashboards: {', '.join(dashboard_titles)}")
                    return True
                else:
                    self.log_test("Grafana Dashboards", "WARN", 
                                f"Found only {len(whisperengine_dashboards)} WhisperEngine dashboards")
                    return False
            else:
                self.log_test("Grafana Dashboards", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Grafana Dashboards", "FAIL", f"Error: {e}")
            return False
    
    def test_influxdb_data_query(self) -> bool:
        """Test InfluxDB data query capabilities"""
        try:
            # Simple query to check if temporal intelligence bucket exists and has data
            headers = {
                'Authorization': f'Token {self.influxdb_token}',
                'Content-Type': 'application/vnd.flux'
            }
            
            # Check for recent data in the last hour
            flux_query = '''
                from(bucket: "temporal_intelligence")
                |> range(start: -1h)
                |> limit(n: 10)
                |> count()
            '''
            
            response = requests.post(
                f"{self.influxdb_url}/api/v2/query?org=whisperengine",
                headers=headers,
                data=flux_query,
                timeout=10
            )
            
            if response.status_code == 200:
                # Check if we got data back
                response_text = response.text.strip()
                if response_text and not response_text.startswith('error'):
                    self.log_test("InfluxDB Data Query", "PASS", "Successfully queried temporal intelligence bucket")
                    return True
                else:
                    self.log_test("InfluxDB Data Query", "WARN", "Bucket accessible but no recent data found")
                    return False
            else:
                self.log_test("InfluxDB Data Query", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("InfluxDB Data Query", "FAIL", f"Error: {e}")
            return False
    
    async def test_end_to_end_monitoring(self) -> bool:
        """Test complete end-to-end monitoring pipeline"""
        try:
            print("\n🔄 Running end-to-end monitoring pipeline test...")
            
            # 1. Send test messages to trigger metrics
            test_messages = [
                "Tell me about marine biology",
                "What's your favorite memory?", 
                "How do emotions work in AI?"
            ]
            
            metrics_triggered = 0
            async with aiohttp.ClientSession() as session:
                for i, message in enumerate(test_messages):
                    test_data = {
                        "user_id": f"e2e_test_user_{i}",
                        "message": message,
                        "context": {"platform": "e2e_monitoring_test"}
                    }
                    
                    try:
                        async with session.post(f"{self.elena_bot_url}/api/chat", 
                                              json=test_data) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get('processing_time_ms', 0) > 0:
                                    metrics_triggered += 1
                                    print(f"   ✅ Message {i+1}: Metrics recorded ({data.get('processing_time_ms')}ms)")
                            
                            # Small delay between messages
                            await asyncio.sleep(1)
                    except Exception as e:
                        print(f"   ❌ Message {i+1}: Failed - {e}")
            
            if metrics_triggered >= 2:
                self.log_test("End-to-End Monitoring", "PASS", 
                            f"Successfully triggered metrics for {metrics_triggered}/{len(test_messages)} test messages")
                return True
            else:
                self.log_test("End-to-End Monitoring", "FAIL", 
                            f"Only triggered metrics for {metrics_triggered}/{len(test_messages)} test messages")
                return False
                
        except Exception as e:
            self.log_test("End-to-End Monitoring", "FAIL", f"Error: {e}")
            return False
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring validation report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "monitoring_validation_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warned_tests,
                "success_rate": f"{success_rate:.1f}%",
                "validation_timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "monitoring_stack_status": {
                "influxdb_healthy": any(r['test'] == 'InfluxDB Health Check' and r['status'] == 'PASS' for r in self.test_results),
                "grafana_healthy": any(r['test'] == 'Grafana Health Check' and r['status'] == 'PASS' for r in self.test_results),
                "character_bots_healthy": any(r['test'].endswith('Bot Health') and r['status'] == 'PASS' for r in self.test_results),
                "metrics_collection_working": any(r['test'] == 'Metrics Collection Test' and r['status'] == 'PASS' for r in self.test_results)
            },
            "recommendations": self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for specific failure patterns
        failed_tests = [r for r in self.test_results if r['status'] == 'FAIL']
        
        if any('InfluxDB' in r['test'] for r in failed_tests):
            recommendations.append("⚠️  InfluxDB issues detected - check docker logs for whisperengine-influxdb")
        
        if any('Grafana' in r['test'] for r in failed_tests):
            recommendations.append("⚠️  Grafana issues detected - verify Grafana container and port 3000 availability")
        
        if any('Bot Health' in r['test'] for r in failed_tests):
            recommendations.append("⚠️  Character bot health issues - check bot container logs and ensure .env files are configured")
        
        if any('Metrics Collection' in r['test'] for r in failed_tests):
            recommendations.append("⚠️  Metrics collection failing - verify InfluxDB integration in character bots")
        
        # Success recommendations
        success_rate = len([r for r in self.test_results if r['status'] == 'PASS']) / len(self.test_results) * 100
        if success_rate >= 80:
            recommendations.append("✅ Monitoring stack is healthy - dashboards should be fully functional")
            recommendations.append("📊 Access Grafana dashboards at http://localhost:3002")
        elif success_rate >= 60:
            recommendations.append("⚠️  Monitoring stack partially functional - some features may be limited")
        else:
            recommendations.append("❌ Monitoring stack needs attention - multiple components failing")
        
        return recommendations

async def main():
    """Main monitoring validation execution"""
    print("🎯 WhisperEngine Real-Time Monitoring Validation")
    print("=" * 55)
    print()
    
    validator = MonitoringStackValidator()
    
    # Run all validation tests
    print("🔍 Testing infrastructure health...")
    await validator.test_influxdb_health()
    await validator.test_grafana_health()
    
    print("\n🤖 Testing character bot health...")
    await validator.test_character_bot_health()
    
    print("\n📊 Testing monitoring capabilities...")
    await validator.test_metrics_collection()
    validator.test_influxdb_data_query()
    validator.test_grafana_dashboards()
    
    print("\n🔄 Testing end-to-end monitoring...")
    await validator.test_end_to_end_monitoring()
    
    # Generate and display report
    print("\n" + "=" * 55)
    print("📈 MONITORING VALIDATION REPORT")
    print("=" * 55)
    
    report = validator.generate_monitoring_report()
    
    # Display summary
    summary = report['monitoring_validation_summary']
    print(f"🎯 Overall Success Rate: {summary['success_rate']}")
    print(f"✅ Tests Passed: {summary['passed']}/{summary['total_tests']}")
    print(f"❌ Tests Failed: {summary['failed']}/{summary['total_tests']}")
    print(f"⚠️  Warnings: {summary['warnings']}/{summary['total_tests']}")
    
    # Display recommendations
    print("\n📋 Recommendations:")
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    # Save detailed report
    with open('monitoring_validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("\n📄 Detailed report saved to: monitoring_validation_report.json")
    
    # Exit with appropriate code
    if summary['failed'] == 0:
        print("\n🎉 All monitoring systems validated successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {summary['failed']} test(s) failed - monitoring may be partially functional")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())