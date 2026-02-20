"""
Token Estimation Utility for AI Models.

Provides accurate token counting and estimation for various AI models.
"""

import re
from typing import Dict, List, Optional


class TokenEstimator:
    """
    Token estimation utility for AI models.
    
    Uses model-specific tokenization rules for accurate estimation.
    Falls back to character-based heuristics when tiktoken is unavailable.
    """
    
    # Average characters per token by model family
    CHARS_PER_TOKEN = {
        "gemini": 4,  # Gemini models
        "gpt": 4,     # GPT models
        "claude": 3.5,  # Claude models
        "default": 4,
    }
    
    # Code-specific character ratios (code has more tokens per char)
    CODE_CHARS_PER_TOKEN = 3.0
    
    def __init__(self, model: str = "gemini-1.5-flash"):
        """Initialize the token estimator."""
        self.model = model
        self.model_family = self._get_model_family(model)
        self.chars_per_token = self.CHARS_PER_TOKEN.get(
            self.model_family, 
            self.CHARS_PER_TOKEN["default"]
        )
    
    def _get_model_family(self, model: str) -> str:
        """Determine the model family from model name."""
        model_lower = model.lower()
        if "gemini" in model_lower:
            return "gemini"
        elif "gpt" in model_lower:
            return "gpt"
        elif "claude" in model_lower:
            return "claude"
        return "default"
    
    def estimate(self, text: str, is_code: bool = False) -> int:
        """
        Estimate the number of tokens in a text.
        
        Args:
            text: Text to estimate tokens for
            is_code: Whether the text is code (uses different ratio)
            
        Returns:
            Estimated number of tokens
        """
        if not text:
            return 0
        
        # Use code-specific ratio if needed
        ratio = self.CODE_CHARS_PER_TOKEN if is_code else self.chars_per_token
        
        # Basic estimation
        estimated = len(text) / ratio
        
        # Account for special characters and whitespace
        # Whitespace-heavy text typically has more tokens
        whitespace_ratio = len(re.findall(r'\s', text)) / max(len(text), 1)
        estimated *= (1 + whitespace_ratio * 0.1)
        
        return int(estimated)
    
    def estimate_messages(self, messages: List[Dict[str, str]]) -> int:
        """
        Estimate tokens for a list of chat messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Estimated total tokens
        """
        total = 0
        
        for message in messages:
            # Each message has overhead for role, content markers
            role = message.get("role", "")
            content = message.get("content", "")
            
            # Role tokens (usually 1-2 tokens)
            total += 2
            
            # Content tokens
            total += self.estimate(content)
            
            # Message overhead (formatting tokens)
            total += 4
        
        # Base overhead for the conversation
        total += 3
        
        return total
    
    def estimate_code_file(
        self, 
        content: str, 
        file_path: Optional[str] = None
    ) -> int:
        """
        Estimate tokens for a code file.
        
        Args:
            content: File content
            file_path: Optional file path for language detection
            
        Returns:
            Estimated number of tokens
        """
        # Determine if it's actually code
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp',
            '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift',
            '.kt', '.scala', '.sh', '.bash', '.zsh', '.ps1',
        }
        
        is_code = False
        if file_path:
            ext = '.' + file_path.rsplit('.', 1)[-1] if '.' in file_path else ''
            is_code = ext.lower() in code_extensions
        else:
            # Heuristic: check for common code patterns
            code_patterns = [
                r'\bfunction\b', r'\bclass\b', r'\bimport\b',
                r'\bconst\b', r'\blet\b', r'\bvar\b',
                r'\bdef\b', r'\breturn\b', r'\{.*\}',
            ]
            is_code = any(re.search(p, content) for p in code_patterns)
        
        return self.estimate(content, is_code=is_code)
    
    def estimate_repository(
        self,
        files: Dict[str, str],
        max_files: int = 100
    ) -> Dict[str, int]:
        """
        Estimate total tokens for a repository.
        
        Args:
            files: Dictionary of file_path -> content
            max_files: Maximum number of files to process
            
        Returns:
            Dictionary with token estimates
        """
        total_tokens = 0
        file_estimates = {}
        
        # Sort files by importance (prefer main code files)
        priority_files = []
        other_files = []
        
        for path, content in list(files.items())[:max_files]:
            if any(p in path.lower() for p in ['main', 'index', 'app', 'server']):
                priority_files.append((path, content))
            else:
                other_files.append((path, content))
        
        # Process priority files first
        for path, content in priority_files + other_files:
            tokens = self.estimate_code_file(content, path)
            file_estimates[path] = tokens
            total_tokens += tokens
        
        return {
            "total_tokens": total_tokens,
            "file_count": len(file_estimates),
            "file_estimates": file_estimates,
        }
    
    def calculate_complexity(self, content: str) -> float:
        """
        Calculate complexity score for content (0-1).
        
        Higher scores indicate more complex content that may benefit
        from a more capable model.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Complexity score from 0 to 1
        """
        if not content:
            return 0.0
        
        score = 0.0
        
        # Length factor
        length = len(content)
        if length > 10000:
            score += 0.2
        elif length > 5000:
            score += 0.1
        
        # Code complexity indicators
        code_patterns = [
            (r'\bclass\b', 0.1),
            (r'\binterface\b', 0.1),
            (r'\basync\b', 0.05),
            (r'\bawait\b', 0.05),
            (r'\bfunction\b', 0.05),
            (r'=>', 0.05),
            (r'\btry\b.*\bcatch\b', 0.1),
            (r'\bimport\b.*\bfrom\b', 0.05),
        ]
        
        for pattern, weight in code_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score += weight
        
        # Nesting depth (approximation)
        max_indent = 0
        for line in content.split('\n'):
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
        
        if max_indent > 16:
            score += 0.15
        elif max_indent > 8:
            score += 0.1
        
        # Comment ratio (well-documented code is often simpler)
        comment_lines = len(re.findall(r'^\s*(#|//|/\*|\*)', content, re.MULTILINE))
        total_lines = len(content.split('\n'))
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio > 0.2:
                score -= 0.05  # Well documented, likely simpler
        
        return min(max(score, 0.0), 1.0)


def estimate_tokens(text: str, model: str = "gemini-1.5-flash") -> int:
    """
    Convenience function to estimate tokens.
    
    Args:
        text: Text to estimate
        model: Model name
        
    Returns:
        Estimated token count
    """
    estimator = TokenEstimator(model)
    return estimator.estimate(text)


def estimate_complexity(content: str) -> float:
    """
    Convenience function to calculate complexity.
    
    Args:
        content: Content to analyze
        
    Returns:
        Complexity score (0-1)
    """
    estimator = TokenEstimator()
    return estimator.calculate_complexity(content)