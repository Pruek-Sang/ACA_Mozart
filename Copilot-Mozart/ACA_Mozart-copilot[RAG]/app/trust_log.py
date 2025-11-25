"""
Trust Log - The Chronicle of Divine Actions
Records every MCP spec generation for audit and learning

Philosophy: Canonical Funnel Trust Records
- Every action recorded
- Full context preserved
- Privacy-compliant (no PII beyond necessary)
- Queryable for regression analysis
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from app.models import McpSpecTrustRecord
from app.config import settings

logger = logging.getLogger("Aura.TrustLog")


class TrustLogger:
    """
    Service for logging MCP spec generation trust records
    
    Storage format: JSONL (one record per line)
    File pattern: logs/mcp_spec/YYYY-MM-DD.jsonl
    
    Why JSONL?
    - Easy to append (no need to load entire file)
    - Each line is valid JSON (easy to parse)
    - Grep-friendly for quick searches
    - Standard for ML training datasets
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize trust logger
        
        Args:
            log_dir: Directory for trust logs (defaults to config)
        """
        self.log_dir = Path(log_dir or settings.TRUST_LOG_DIR)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Trust logger initialized: {self.log_dir}")
    
    def _get_log_file_path(self, timestamp: Optional[datetime] = None) -> Path:
        """
        Get log file path for a given timestamp
        
        Args:
            timestamp: Timestamp (defaults to now)
        
        Returns:
            Path to log file
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        date_str = timestamp.strftime("%Y-%m-%d")
        return self.log_dir / f"{date_str}.jsonl"
    
    def log_mcp_spec(self, record: McpSpecTrustRecord) -> bool:
        """
        Log an MCP spec generation record
        
        Args:
            record: Trust record to log
        
        Returns:
            True if logged successfully
        """
        try:
            log_file = self._get_log_file_path(record.timestamp)
            
            # Convert to JSON
            record_json = record.model_dump()
            record_line = json.dumps(record_json, ensure_ascii=False)
            
            # Append to file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(record_line + '\n')
            
            logger.debug(f"Logged trust record: {record.request_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log trust record: {e}")
            return False
    
    def create_record(
        self,
        project_requirements: dict,
        retrieved_doc_ids: list,
        llm_model: str,
        raw_llm_output: str,
        parse_success: bool,
        validation_errors: Optional[list] = None,
        project_input: Optional[dict] = None,
        user_id: Optional[str] = None,
        forwarded_to_mcp: bool = False
    ) -> McpSpecTrustRecord:
        """
        Create a trust record (helper method)
        
        Args:
            project_requirements: Raw input requirements
            retrieved_doc_ids: Document IDs used for context
            llm_model: LLM model name
            raw_llm_output: Raw LLM response
            parse_success: Did parsing succeed?
            validation_errors: List of validation errors if any
            project_input: Parsed ProjectInputSpec if successful
            user_id: User ID if available
            forwarded_to_mcp: Was this sent to MCP?
        
        Returns:
            Trust record ready to log
        """
        return McpSpecTrustRecord(
            timestamp=datetime.utcnow(),
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            project_requirements=project_requirements,
            retrieved_doc_ids=retrieved_doc_ids,
            llm_model=llm_model,
            raw_llm_output=raw_llm_output,
            parse_success=parse_success,
            validation_errors=validation_errors or [],
            project_input=project_input,
            forwarded_to_mcp=forwarded_to_mcp
        )
    
    def read_records(
        self,
        date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> list:
        """
        Read trust records from log file
        
        Args:
            date: Date to read (defaults to today)
            limit: Maximum number of records to return
        
        Returns:
            List of trust records
        """
        try:
            log_file = self._get_log_file_path(date)
            
            if not log_file.exists():
                logger.warning(f"Log file not found: {log_file}")
                return []
            
            records = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record_json = json.loads(line)
                        records.append(record_json)
                        
                        if limit and len(records) >= limit:
                            break
            
            logger.info(f"Read {len(records)} records from {log_file}")
            return records
            
        except Exception as e:
            logger.error(f"Failed to read trust records: {e}")
            return []
    
    def cleanup_old_logs(self, retention_days: Optional[int] = None) -> int:
        """
        Remove log files older than retention period
        
        Args:
            retention_days: Number of days to keep (defaults to config)
        
        Returns:
            Number of files deleted
        """
        if retention_days is None:
            retention_days = settings.TRUST_LOG_RETENTION_DAYS
        
        try:
            cutoff_date = datetime.utcnow().timestamp() - (retention_days * 86400)
            deleted_count = 0
            
            for log_file in self.log_dir.glob("*.jsonl"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file}")
            
            logger.info(f"Cleanup complete: {deleted_count} files deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0


# Global trust logger instance
trust_logger = TrustLogger()
