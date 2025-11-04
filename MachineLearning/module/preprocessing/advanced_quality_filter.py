"""
Advanced Quality Filter for Code

Uses multiple metrics to assess code quality:
- Cyclomatic Complexity (McCabe)
- Maintainability Index
- Halstead metrics
- Docstring presence
- Line count
- Comment ratio

Requires: pip install radon

Version 1.2.0
"""

import logging
import ast
from typing import Dict, Optional
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit
from radon.raw import analyze

logger = logging.getLogger(__name__)


class AdvancedQualityFilter:
    """
    Advanced quality filter using multiple code metrics.
    
    Score range: 0-100
    - 80-100: Excellent (clean, maintainable, well-documented)
    - 60-79:  Good (acceptable for training)
    - 40-59:  Fair (may have issues)
    - 0-39:   Poor (skip)
    """
    
    def __init__(self, 
                 min_score: int = 60,
                 max_complexity: int = 15,
                 min_maintainability: int = 20,
                 min_lines: int = 5,
                 max_lines: int = 300):
        """
        Initialize quality filter with thresholds.
        
        Args:
            min_score: Minimum quality score (0-100) to accept
            max_complexity: Maximum cyclomatic complexity per function
            min_maintainability: Minimum maintainability index
            min_lines: Minimum lines of code
            max_lines: Maximum lines of code
        """
        self.min_score = min_score
        self.max_complexity = max_complexity
        self.min_maintainability = min_maintainability
        self.min_lines = min_lines
        self.max_lines = max_lines
        
        logger.info(f"AdvancedQualityFilter initialized (min_score={min_score})")
    
    def calculate_quality_score(self, code: str) -> Dict[str, any]:
        """
        Calculate comprehensive quality score for code.
        
        Scoring breakdown:
        - Complexity (30 points): Lower complexity = higher score
        - Maintainability (25 points): MI score converted to points
        - Documentation (20 points): Docstrings, comments
        - Length (15 points): Optimal length range
        - Halstead (10 points): Code difficulty metrics
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dict with score and detailed metrics:
            {
                'total_score': 85,
                'complexity_score': 28,
                'maintainability_score': 23,
                'documentation_score': 18,
                'length_score': 12,
                'halstead_score': 4,
                'metrics': {...},
                'passed': True
            }
        """
        scores = {
            'total_score': 0,
            'complexity_score': 0,
            'maintainability_score': 0,
            'documentation_score': 0,
            'length_score': 0,
            'halstead_score': 0,
            'metrics': {},
            'passed': False
        }
        
        try:
            # 1. COMPLEXITY ANALYSIS (30 points max)
            complexity_score = self._score_complexity(code)
            scores['complexity_score'] = complexity_score
            
            # 2. MAINTAINABILITY INDEX (25 points max)
            maintainability_score = self._score_maintainability(code)
            scores['maintainability_score'] = maintainability_score
            
            # 3. DOCUMENTATION (20 points max)
            documentation_score = self._score_documentation(code)
            scores['documentation_score'] = documentation_score
            
            # 4. LENGTH (15 points max)
            length_score = self._score_length(code)
            scores['length_score'] = length_score
            
            # 5. HALSTEAD METRICS (10 points max)
            halstead_score = self._score_halstead(code)
            scores['halstead_score'] = halstead_score
            
            # Calculate total
            scores['total_score'] = (
                complexity_score +
                maintainability_score +
                documentation_score +
                length_score +
                halstead_score
            )
            
            # Pass/fail
            scores['passed'] = scores['total_score'] >= self.min_score
            
        except Exception as e:
            logger.debug(f"Quality scoring failed: {e}")
            scores['total_score'] = 0
            scores['passed'] = False
        
        return scores
    
    def _score_complexity(self, code: str) -> float:
        """
        Score based on cyclomatic complexity (30 points max).
        
        Complexity interpretation:
        - 1-5: Simple (30 points)
        - 6-10: Moderate (20 points)
        - 11-15: Complex (10 points)
        - 16+: Very complex (0 points)
        """
        try:
            cc_results = cc_visit(code)
            
            if not cc_results:
                return 15  # Neutral score for empty/simple code
            
            # Average complexity across all functions/classes
            avg_complexity = sum(item.complexity for item in cc_results) / len(cc_results)
            
            # Store metric
            self.metrics = {'avg_complexity': avg_complexity}
            
            # Score mapping
            if avg_complexity <= 5:
                return 30
            elif avg_complexity <= 10:
                return 20
            elif avg_complexity <= self.max_complexity:
                return 10
            else:
                return 0
                
        except Exception as e:
            logger.debug(f"Complexity analysis failed: {e}")
            return 0
    
    def _score_maintainability(self, code: str) -> float:
        """
        Score based on Maintainability Index (25 points max).
        
        MI interpretation:
        - 80-100: Highly maintainable (25 points)
        - 60-79: Maintainable (20 points)
        - 40-59: Moderate (15 points)
        - 20-39: Low maintainability (10 points)
        - 0-19: Difficult to maintain (0 points)
        """
        try:
            mi_score = mi_visit(code, multi=False)
            
            # Normalize to 0-25 scale
            if mi_score >= 80:
                return 25
            elif mi_score >= 60:
                return 20
            elif mi_score >= 40:
                return 15
            elif mi_score >= self.min_maintainability:
                return 10
            else:
                return 0
                
        except Exception as e:
            logger.debug(f"Maintainability analysis failed: {e}")
            return 0
    
    def _score_documentation(self, code: str) -> float:
        """
        Score based on documentation quality (20 points max).
        
        Factors:
        - Docstrings present (+10)
        - Comment ratio 5-20% (+10)
        - Type hints present (+5 bonus)
        """
        score = 0
        
        try:
            # Check for docstrings (triple quotes)
            if '"""' in code or "'''" in code:
                score += 10
            
            # Calculate comment ratio
            lines = code.split('\n')
            total_lines = len(lines)
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            
            if total_lines > 0:
                comment_ratio = comment_lines / total_lines
                
                # Optimal range: 5-20%
                if 0.05 <= comment_ratio <= 0.20:
                    score += 10
                elif 0.01 <= comment_ratio <= 0.30:
                    score += 5
            
            # Bonus: Check for type hints
            if '->' in code or ': ' in code:
                # Verify it's actually type hints, not just string with ->
                try:
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if node.returns or any(arg.annotation for arg in node.args.args):
                                score += 5
                                break
                except:
                    pass
            
        except Exception as e:
            logger.debug(f"Documentation analysis failed: {e}")
        
        return min(score, 20)
    
    def _score_length(self, code: str) -> float:
        """
        Score based on code length (15 points max).
        
        Optimal range: 20-200 lines
        - Too short (<10): Trivial (5 points)
        - Optimal (20-200): Good length (15 points)
        - Too long (>300): Hard to understand (0 points)
        """
        lines = len([l for l in code.split('\n') if l.strip()])
        
        if lines < 10:
            return 5
        elif self.min_lines <= lines <= self.max_lines:
            return 15
        elif lines <= self.max_lines * 1.5:
            return 10
        else:
            return 0
    
    def _score_halstead(self, code: str) -> float:
        """
        Score based on Halstead metrics (10 points max).
        
        Halstead difficulty:
        - Low difficulty (<10): Easy to understand (10 points)
        - Medium (10-20): Acceptable (7 points)
        - High (20-30): Complex (4 points)
        - Very high (>30): Hard to maintain (0 points)
        """
        try:
            halstead = h_visit(code)
            
            if not halstead:
                return 5
            
            # Get average difficulty
            difficulties = [item.difficulty for item in halstead]
            if not difficulties:
                return 5
            
            avg_difficulty = sum(difficulties) / len(difficulties)
            
            if avg_difficulty < 10:
                return 10
            elif avg_difficulty < 20:
                return 7
            elif avg_difficulty < 30:
                return 4
            else:
                return 0
                
        except Exception as e:
            logger.debug(f"Halstead analysis failed: {e}")
            return 5
    
    def is_valid_code(self, code: str) -> bool:
        """
        Check if code meets minimum quality threshold.
        
        Args:
            code: Python code to validate
            
        Returns:
            True if code passes quality check
        """
        if not code or not code.strip():
            return False
        
        # Calculate score
        result = self.calculate_quality_score(code)
        
        return result['passed']
    
    def get_detailed_report(self, code: str) -> str:
        """
        Get human-readable quality report.
        
        Args:
            code: Code to analyze
            
        Returns:
            Formatted report string
        """
        result = self.calculate_quality_score(code)
        
        report = f"""
Quality Report
{'='*50}
Total Score: {result['total_score']:.1f}/100 {'✅ PASS' if result['passed'] else '❌ FAIL'}

Breakdown:
  Complexity:      {result['complexity_score']:.1f}/30
  Maintainability: {result['maintainability_score']:.1f}/25
  Documentation:   {result['documentation_score']:.1f}/20
  Length:          {result['length_score']:.1f}/15
  Halstead:        {result['halstead_score']:.1f}/10

Recommendation: {'Accept for training' if result['passed'] else 'Skip - quality too low'}
"""
        return report


# Backward compatibility: Simple wrapper
class QualityFilter:
    """
    Simple quality filter (backward compatible).
    Uses AdvancedQualityFilter under the hood.
    """
    
    def __init__(self, min_score: int = 60):
        self.advanced_filter = AdvancedQualityFilter(min_score=min_score)
    
    def is_valid_code(self, code: str) -> bool:
        """Check if code is valid (backward compatible method)."""
        return self.advanced_filter.is_valid_code(code)
