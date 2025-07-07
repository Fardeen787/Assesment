from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any, List  # Added List import here
import json
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Handles audit logging for HIPAA compliance
    Logs all access, modifications, and searches on medical records
    """
    
    def __init__(self):
        self.enabled = True
        self.log_level = "INFO"
    
    def log_user_action(self, db: Session, user_id: int, action: str, 
                       resource_type: str, resource_id: Optional[int] = None,
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                       data: Optional[Dict[str, Any]] = None):
        """
        Log a user action to the audit trail
        """
        if not self.enabled:
            return
        
        try:
            # Import here to avoid circular imports
            from models import AuditLog
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data=json.dumps(data) if data else None,
                timestamp=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Audit log created: User {user_id} performed {action} on {resource_type}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't fail the main operation if audit logging fails
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       duration: float, user_id: Optional[int] = None):
        """
        Log API request metrics
        """
        logger.info(
            f"API Request: {method} {path} - Status: {status_code} - "
            f"Duration: {duration:.3f}s - User: {user_id or 'Anonymous'}"
        )
    
    def log_data_access(self, db: Session, user_id: int, 
                       access_type: str, patient_id: int,
                       fields_accessed: List[str], purpose: str):
        """
        Log detailed data access for HIPAA minimum necessary standard
        """
        data = {
            "access_type": access_type,
            "fields_accessed": fields_accessed,
            "purpose": purpose
        }
        
        self.log_user_action(
            db=db,
            user_id=user_id,
            action="data_access",
            resource_type="patient_data",
            resource_id=patient_id,
            data=data
        )
    
    def log_security_event(self, db: Session, event_type: str, 
                          description: str, user_id: Optional[int] = None,
                          severity: str = "INFO"):
        """
        Log security-related events
        """
        data = {
            "event_type": event_type,
            "description": description,
            "severity": severity
        }
        
        self.log_user_action(
            db=db,
            user_id=user_id or 0,  # Use 0 for system events
            action="security_event",
            resource_type="system",
            data=data
        )
        
        # Also log to application logger
        log_method = getattr(logger, severity.lower(), logger.info)
        log_method(f"Security Event [{event_type}]: {description}")
    
    def generate_audit_report(self, db: Session, start_date: datetime, 
                            end_date: datetime, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate an audit report for a given time period
        """
        from models import AuditLog
        
        query = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        logs = query.all()
        
        # Aggregate data
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_actions": len(logs),
            "actions_by_type": {},
            "actions_by_resource": {},
            "actions_by_user": {},
            "security_events": []
        }
        
        for log in logs:
            # Count by action type
            report["actions_by_type"][log.action] = report["actions_by_type"].get(log.action, 0) + 1
            
            # Count by resource type
            report["actions_by_resource"][log.resource_type] = report["actions_by_resource"].get(log.resource_type, 0) + 1
            
            # Count by user
            report["actions_by_user"][log.user_id] = report["actions_by_user"].get(log.user_id, 0) + 1
            
            # Collect security events
            if log.action == "security_event":
                report["security_events"].append({
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "details": json.loads(log.additional_data) if log.additional_data else {}
                })
        
        return report
