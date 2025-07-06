#!/usr/bin/env python3
import json
import re
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import argparse

class LogAnalyzer:
    """Comprehensive log analysis tool"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_files = {
            'all': self.log_dir / "smart-dashboard.log",
            'errors': self.log_dir / "smart-dashboard_errors.log",
            'json': self.log_dir / "smart-dashboard_structured.json"
        }
    
    def read_plain_logs(self, log_file: str = 'all') -> List[Dict[str, Any]]:
        """Read and parse plain text log files"""
        file_path = self.log_files.get(log_file)
        if not file_path or not file_path.exists():
            print(f"Log file {file_path} not found!")
            return []
        
        logs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Parse log line: timestamp - level - module:function:line - message
                match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - ([^:]+):([^:]+):(\d+) - (.+)', line)
                if match:
                    timestamp, level, module, function, line_num, message = match.groups()
                    logs.append({
                        'timestamp': timestamp,
                        'level': level,
                        'module': module,
                        'function': function,
                        'line': int(line_num),
                        'message': message,
                        'raw': line
                    })
                else:
                    # Fallback for lines that don't match the pattern
                    logs.append({
                        'timestamp': None,
                        'level': 'UNKNOWN',
                        'module': 'unknown',
                        'function': 'unknown',
                        'line': 0,
                        'message': line,
                        'raw': line
                    })
        
        return logs
    
    def read_json_logs(self) -> List[Dict[str, Any]]:
        """Read and parse JSON log files"""
        file_path = self.log_files['json']
        if not file_path.exists():
            print(f"JSON log file {file_path} not found!")
            return []
        
        logs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON line: {line[:100]}...")
        
        return logs
    
    def filter_logs(self, logs: List[Dict[str, Any]], 
                   level: Optional[str] = None,
                   module: Optional[str] = None,
                   function: Optional[str] = None,
                   start_time: Optional[str] = None,
                   end_time: Optional[str] = None,
                   message_contains: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter logs based on various criteria"""
        filtered = logs
        
        if level:
            filtered = [log for log in filtered if log.get('level', '').upper() == level.upper()]
        
        if module:
            filtered = [log for log in filtered if module.lower() in log.get('module', '').lower()]
        
        if function:
            filtered = [log for log in filtered if function.lower() in log.get('function', '').lower()]
        
        if message_contains:
            filtered = [log for log in filtered if message_contains.lower() in log.get('message', '').lower()]
        
        if start_time or end_time:
            filtered = [log for log in filtered if log.get('timestamp')]
            if start_time:
                filtered = [log for log in filtered if log['timestamp'] >= start_time]
            if end_time:
                filtered = [log for log in filtered if log['timestamp'] <= end_time]
        
        return filtered
    
    def analyze_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze logs and return statistics"""
        if not logs:
            return {}
        
        analysis = {
            'total_logs': len(logs),
            'level_distribution': Counter(),
            'module_distribution': Counter(),
            'function_distribution': Counter(),
            'time_range': {'start': None, 'end': None},
            'error_summary': [],
            'performance_metrics': defaultdict(list)
        }
        
        for log in logs:
            # Level distribution
            level = log.get('level', 'UNKNOWN')
            analysis['level_distribution'][level] += 1
            
            # Module distribution
            module = log.get('module', 'unknown')
            analysis['module_distribution'][module] += 1
            
            # Function distribution
            function = log.get('function', 'unknown')
            analysis['function_distribution'][function] += 1
            
            # Time range
            timestamp = log.get('timestamp')
            if timestamp:
                if not analysis['time_range']['start'] or timestamp < analysis['time_range']['start']:
                    analysis['time_range']['start'] = timestamp
                if not analysis['time_range']['end'] or timestamp > analysis['time_range']['end']:
                    analysis['time_range']['end'] = timestamp
            
            # Error summary
            if level in ['ERROR', 'CRITICAL']:
                analysis['error_summary'].append({
                    'timestamp': timestamp,
                    'module': module,
                    'function': function,
                    'message': log.get('message', '')
                })
            
            # Performance metrics (extract from specialized logs)
            message = log.get('message', '')
            
            # HTTP request timing
            request_match = re.search(r'(\w+) ([^\s]+) - (\d+) \((\d+\.\d+)s\)', message)
            if request_match:
                method, url, status, duration = request_match.groups()
                analysis['performance_metrics']['http_requests'].append({
                    'method': method,
                    'url': url,
                    'status': int(status),
                    'duration': float(duration)
                })
            
            # Database operation timing
            db_match = re.search(r'DB (\w+) on (\w+) - (\w+) \((\d+\.\d+)s\)', message)
            if db_match:
                operation, collection, status, duration = db_match.groups()
                analysis['performance_metrics']['database_operations'].append({
                    'operation': operation,
                    'collection': collection,
                    'status': status,
                    'duration': float(duration)
                })
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Print analysis results in a formatted way"""
        if not analysis:
            print("No logs to analyze!")
            return
        
        print("\n" + "="*60)
        print("LOG ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n📊 Total Logs: {analysis['total_logs']}")
        
        if analysis['time_range']['start'] and analysis['time_range']['end']:
            print(f"⏰ Time Range: {analysis['time_range']['start']} to {analysis['time_range']['end']}")
        
        # Level distribution
        print(f"\n🎯 Log Levels:")
        for level, count in analysis['level_distribution'].most_common():
            percentage = (count / analysis['total_logs']) * 100
            print(f"  {level}: {count} ({percentage:.1f}%)")
        
        # Module distribution
        print(f"\n📁 Top Modules:")
        for module, count in analysis['module_distribution'].most_common(5):
            percentage = (count / analysis['total_logs']) * 100
            print(f"  {module}: {count} ({percentage:.1f}%)")
        
        # Error summary
        if analysis['error_summary']:
            print(f"\n❌ Recent Errors ({len(analysis['error_summary'])} total):")
            for error in analysis['error_summary'][-5:]:  # Show last 5 errors
                print(f"  {error['timestamp']} - {error['module']}.{error['function']}: {error['message'][:80]}...")
        
        # Performance metrics
        if analysis['performance_metrics']['http_requests']:
            requests = analysis['performance_metrics']['http_requests']
            avg_duration = sum(r['duration'] for r in requests) / len(requests)
            print(f"\n🌐 HTTP Requests: {len(requests)} requests, avg duration: {avg_duration:.3f}s")
        
        if analysis['performance_metrics']['database_operations']:
            db_ops = analysis['performance_metrics']['database_operations']
            avg_duration = sum(op['duration'] for op in db_ops) / len(db_ops)
            print(f"\n🗄️ Database Operations: {len(db_ops)} operations, avg duration: {avg_duration:.3f}s")
    
    def search_logs(self, logs: List[Dict[str, Any]], search_term: str) -> List[Dict[str, Any]]:
        """Search logs for specific terms"""
        results = []
        search_term_lower = search_term.lower()
        
        for log in logs:
            message = log.get('message', '').lower()
            module = log.get('module', '').lower()
            function = log.get('function', '').lower()
            
            if (search_term_lower in message or 
                search_term_lower in module or 
                search_term_lower in function):
                results.append(log)
        
        return results
    
    def export_logs(self, logs: List[Dict[str, Any]], output_file: str, format: str = 'json'):
        """Export filtered logs to a file"""
        output_path = Path(output_file)
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'csv':
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if logs:
                    writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                    writer.writeheader()
                    writer.writerows(logs)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                for log in logs:
                    f.write(log.get('raw', str(log)) + '\n')
        
        print(f"Exported {len(logs)} logs to {output_path}")

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Analyze Smart Dashboard logs')
    parser.add_argument('--log-dir', default='logs', help='Log directory path')
    parser.add_argument('--file', choices=['all', 'errors', 'json'], default='all', 
                       help='Which log file to analyze')
    parser.add_argument('--level', help='Filter by log level')
    parser.add_argument('--module', help='Filter by module name')
    parser.add_argument('--function', help='Filter by function name')
    parser.add_argument('--start-time', help='Filter logs from this time (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end-time', help='Filter logs until this time (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--search', help='Search for term in messages')
    parser.add_argument('--export', help='Export filtered logs to file')
    parser.add_argument('--format', choices=['json', 'csv', 'txt'], default='json',
                       help='Export format')
    parser.add_argument('--limit', type=int, help='Limit number of results')
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer(args.log_dir)
    
    # Read logs
    if args.file == 'json':
        logs = analyzer.read_json_logs()
    else:
        logs = analyzer.read_plain_logs(args.file)
    
    if not logs:
        print("No logs found!")
        return
    
    # Filter logs
    filtered_logs = analyzer.filter_logs(
        logs,
        level=args.level,
        module=args.module,
        function=args.function,
        start_time=args.start_time,
        end_time=args.end_time,
        message_contains=args.search
    )
    
    # Apply limit
    if args.limit:
        filtered_logs = filtered_logs[-args.limit:]
    
    # Export if requested
    if args.export:
        analyzer.export_logs(filtered_logs, args.export, args.format)
    
    # Analyze and display
    analysis = analyzer.analyze_logs(filtered_logs)
    analyzer.print_analysis(analysis)
    
    # Show sample logs
    if filtered_logs:
        print(f"\n📋 Sample Logs (showing last {min(5, len(filtered_logs))}):")
        for log in filtered_logs[-5:]:
            timestamp = log.get('timestamp', 'N/A')
            level = log.get('level', 'UNKNOWN')
            module = log.get('module', 'unknown')
            message = log.get('message', '')[:80]
            print(f"  {timestamp} [{level}] {module}: {message}...")

if __name__ == "__main__":
    main() 