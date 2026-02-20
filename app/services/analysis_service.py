"""
Analysis service for repository analysis orchestration.
Coordinates between GitHub, AI, and database operations.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from app.config import settings
from app.supabase_client import supabase


class AnalysisError(Exception):
    """Raised when analysis operations fail."""
    pass


class AnalysisService:
    """
    Analysis orchestration service.
    
    Coordinates repository analysis workflow including:
    - Creating analysis records
    - Queueing background jobs
    - Processing and storing results
    """
    
    def __init__(self):
        """Initialize analysis service."""
        pass
    
    async def create_analysis(
        self,
        repository_id: str,
        analysis_type: str,
        triggered_by: str,
    ) -> dict[str, Any]:
        """
        Create a new analysis record.
        
        Args:
            repository_id: UUID of the repository.
            analysis_type: Type of analysis (full, security, performance, ci_cd).
            triggered_by: UUID of the user triggering the analysis.
        
        Returns:
            Created analysis record.
        
        Raises:
            AnalysisError: If creation fails.
        """
        try:
            analysis_data = {
                "repository_id": repository_id,
                "analysis_type": analysis_type,
                "status": "pending",
                "triggered_by": triggered_by,
            }
            
            response = supabase.table("analyses").insert(analysis_data).execute()
            
            if not response.data:
                raise AnalysisError("Failed to create analysis record")
            
            return response.data[0]
        
        except Exception as e:
            raise AnalysisError(f"Failed to create analysis: {e}")
    
    async def get_analysis(self, analysis_id: str) -> Optional[dict[str, Any]]:
        """
        Get an analysis record by ID.
        
        Args:
            analysis_id: UUID of the analysis.
        
        Returns:
            Analysis record or None if not found.
        """
        try:
            response = supabase.table("analyses").select("*").eq("id", analysis_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception:
            return None
    
    async def get_repository_analyses(
        self,
        repository_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get analyses for a repository.
        
        Args:
            repository_id: UUID of the repository.
            limit: Maximum number of records to return.
            offset: Number of records to skip.
        
        Returns:
            List of analysis records.
        """
        try:
            response = (
                supabase.table("analyses")
                .select("*")
                .eq("repository_id", repository_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            return response.data or []
        
        except Exception:
            return []
    
    async def update_analysis_status(
        self,
        analysis_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update analysis status.
        
        Args:
            analysis_id: UUID of the analysis.
            status: New status (pending, in_progress, completed, failed).
            started_at: When analysis started.
            completed_at: When analysis completed.
            error_message: Error message if failed.
        
        Returns:
            Updated analysis record.
        
        Raises:
            AnalysisError: If update fails.
        """
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
            
            if started_at:
                update_data["started_at"] = started_at.isoformat()
            
            if completed_at:
                update_data["completed_at"] = completed_at.isoformat()
            
            if error_message:
                update_data["error_message"] = error_message
            
            response = (
                supabase.table("analyses")
                .update(update_data)
                .eq("id", analysis_id)
                .execute()
            )
            
            if not response.data:
                raise AnalysisError(f"Analysis {analysis_id} not found")
            
            return response.data[0]
        
        except Exception as e:
            raise AnalysisError(f"Failed to update analysis: {e}")
    
    async def store_analysis_results(
        self,
        analysis_id: str,
        results: dict[str, Any],
        model_used: str,
        tokens_used: int,
    ) -> dict[str, Any]:
        """
        Store analysis results.
        
        Args:
            analysis_id: UUID of the analysis.
            results: Analysis results dictionary.
            model_used: AI model used for analysis.
            tokens_used: Number of tokens consumed.
        
        Returns:
            Updated analysis record.
        
        Raises:
            AnalysisError: If storage fails.
        """
        try:
            update_data = {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "results": {
                    **results,
                    "model_used": model_used,
                    "tokens_used": tokens_used,
                },
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            response = (
                supabase.table("analyses")
                .update(update_data)
                .eq("id", analysis_id)
                .execute()
            )
            
            if not response.data:
                raise AnalysisError(f"Analysis {analysis_id} not found")
            
            # Update repository's last_analyzed_at
            analysis = await self.get_analysis(analysis_id)
            if analysis:
                await self._update_repository_analyzed_at(analysis["repository_id"])
            
            return response.data[0]
        
        except Exception as e:
            raise AnalysisError(f"Failed to store results: {e}")
    
    async def _update_repository_analyzed_at(self, repository_id: str) -> None:
        """Update repository's last analyzed timestamp."""
        try:
            supabase.table("repositories").update({
                "last_analyzed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", repository_id).execute()
        except Exception:
            pass  # Non-critical update
    
    async def create_recommendations(
        self,
        analysis_id: str,
        recommendations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Create recommendation records from analysis results.
        
        Args:
            analysis_id: UUID of the analysis.
            recommendations: List of recommendation dictionaries.
        
        Returns:
            Created recommendation records.
        """
        try:
            records = []
            for rec in recommendations:
                records.append({
                    "analysis_id": analysis_id,
                    "category": rec.get("category", "general"),
                    "severity": rec.get("severity", "info"),
                    "title": rec.get("title", ""),
                    "description": rec.get("description", ""),
                    "file_path": rec.get("file_path"),
                    "line_number": rec.get("line_number"),
                    "suggested_fix": rec.get("suggested_fix"),
                })
            
            if records:
                response = supabase.table("recommendations").insert(records).execute()
                return response.data or []
            
            return []
        
        except Exception as e:
            raise AnalysisError(f"Failed to create recommendations: {e}")
    
    async def get_recommendations(
        self,
        analysis_id: str,
        category: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get recommendations for an analysis.
        
        Args:
            analysis_id: UUID of the analysis.
            category: Filter by category.
            severity: Filter by severity.
        
        Returns:
            List of recommendation records.
        """
        try:
            query = supabase.table("recommendations").select("*").eq("analysis_id", analysis_id)
            
            if category:
                query = query.eq("category", category)
            
            if severity:
                query = query.eq("severity", severity)
            
            response = query.order("severity").execute()
            return response.data or []
        
        except Exception:
            return []
    
    async def create_remediation_snippet(
        self,
        analysis_id: str,
        file_path: str,
        original_code: str,
        suggested_code: str,
        explanation: str,
    ) -> dict[str, Any]:
        """
        Create a remediation snippet.
        
        Args:
            analysis_id: UUID of the analysis.
            file_path: Path to the file.
            original_code: Original code block.
            suggested_code: Suggested improved code.
            explanation: Explanation of the change.
        
        Returns:
            Created remediation snippet record.
        """
        try:
            data = {
                "analysis_id": analysis_id,
                "file_path": file_path,
                "original_code": original_code,
                "suggested_code": suggested_code,
                "explanation": explanation,
                "apply_status": "pending",
            }
            
            response = supabase.table("remediation_snippets").insert(data).execute()
            
            if not response.data:
                raise AnalysisError("Failed to create remediation snippet")
            
            return response.data[0]
        
        except Exception as e:
            raise AnalysisError(f"Failed to create remediation snippet: {e}")
    
    async def get_remediation_snippets(
        self,
        analysis_id: str,
    ) -> list[dict[str, Any]]:
        """
        Get remediation snippets for an analysis.
        
        Args:
            analysis_id: UUID of the analysis.
        
        Returns:
            List of remediation snippet records.
        """
        try:
            response = (
                supabase.table("remediation_snippets")
                .select("*")
                .eq("analysis_id", analysis_id)
                .execute()
            )
            return response.data or []
        
        except Exception:
            return []


# Singleton instance
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """Get the singleton analysis service instance."""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service