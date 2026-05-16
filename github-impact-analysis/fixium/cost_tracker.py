"""Track Bob CLI usage costs (coins and dollars)."""
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class CostInfo:
    """Bob CLI cost information."""
    coins_used: float = 0.0
    dollars_used: float = 0.0
    operation: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def format_for_comment(self) -> str:
        """Format cost info for GitHub comment."""
        if self.coins_used == 0.0 and self.dollars_used == 0.0:
            return ""
        
        lines = [
            "### 💰 Cost Information",
            "",
            f"**Bob Coins Used**: {self.coins_used:,.2f} coins",
            f"**Estimated Cost**: ${self.dollars_used:.4f}",
            ""
        ]
        return "\n".join(lines)


class CostTracker:
    """Extract and track Bob CLI costs from command output."""
    
    # Regex patterns to extract cost information from Bob CLI output
    # Pattern for Bob CLI tool output: "[using tool X: ... | Cost: 0.02]"
    BOB_TOOL_COST_PATTERN = re.compile(r'\[using tool.*?Cost:\s*(\d+(?:\.\d+)?)\]', re.IGNORECASE)
    
    # Legacy patterns for other formats
    COIN_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(?:bob\s*)?coins?\s*used', re.IGNORECASE)
    DOLLAR_PATTERN = re.compile(r'\$(\d+(?:\.\d+)?)', re.IGNORECASE)
    COST_SUMMARY_PATTERN = re.compile(
        r'(?:cost|usage|spent).*?(\d+(?:\.\d+)?)\s*(?:bob\s*)?coins?.*?\$(\d+(?:\.\d+)?)',
        re.IGNORECASE | re.DOTALL
    )
    
    @staticmethod
    def extract_costs(output: str, operation: str = "") -> CostInfo:
        """
        Extract cost information from Bob CLI output.
        
        Args:
            output: Bob CLI stdout/stderr output
            operation: Operation name (e.g., "code review", "doc analysis")
            
        Returns:
            CostInfo object with extracted costs
        """
        cost_info = CostInfo(operation=operation)
        
        if not output:
            return cost_info
        
        # Strategy 1: Look for Bob CLI tool cost format "[using tool X: ... | Cost: 0.02]"
        # Bob reports cost in coins, not dollars
        tool_cost_matches = CostTracker.BOB_TOOL_COST_PATTERN.findall(output)
        if tool_cost_matches:
            try:
                # Sum all tool costs (Bob reports coins per tool use)
                total_coins = sum(float(cost) for cost in tool_cost_matches)
                cost_info.coins_used = total_coins
                # Convert to dollars using Bob Pro plan rate: 40 coins = $20, so 2 coins = $1
                cost_info.dollars_used = total_coins / 2
                return cost_info
            except (ValueError, TypeError):
                pass
        
        # Strategy 2: Try to find cost summary (legacy format)
        summary_match = CostTracker.COST_SUMMARY_PATTERN.search(output)
        if summary_match:
            try:
                cost_info.coins_used = float(summary_match.group(1))
                cost_info.dollars_used = float(summary_match.group(2))
                return cost_info
            except (ValueError, IndexError):
                pass
        
        # Fall back to individual pattern matching
        coin_matches = CostTracker.COIN_PATTERN.findall(output)
        if coin_matches:
            try:
                # Take the last match (usually the total)
                cost_info.coins_used = float(coin_matches[-1])
            except (ValueError, IndexError):
                pass
        
        dollar_matches = CostTracker.DOLLAR_PATTERN.findall(output)
        if dollar_matches:
            try:
                # Take the last match (usually the total)
                cost_info.dollars_used = float(dollar_matches[-1])
            except (ValueError, IndexError):
                pass
        
        return cost_info
    
    @staticmethod
    def parse_bob_cost_line(line: str) -> Optional[Tuple[float, float]]:
        """
        Parse a Bob CLI cost line.
        
        Expected formats:
        - "Cost: 123.45 coins ($0.0123)"
        - "Total: 123.45 bob coins, $0.0123"
        - "Used 123.45 coins, cost: $0.0123"
        
        Args:
            line: Single line from Bob CLI output
            
        Returns:
            Tuple of (coins, dollars) or None if not a cost line
        """
        line_lower = line.lower()
        
        # Check if this looks like a cost line
        if not any(keyword in line_lower for keyword in ['cost', 'coins', 'used', 'total', '$']):
            return None
        
        coins = 0.0
        dollars = 0.0
        
        # Extract coins
        coin_match = CostTracker.COIN_PATTERN.search(line)
        if coin_match:
            try:
                coins = float(coin_match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Extract dollars
        dollar_match = CostTracker.DOLLAR_PATTERN.search(line)
        if dollar_match:
            try:
                dollars = float(dollar_match.group(1))
            except (ValueError, IndexError):
                pass
        
        if coins > 0 or dollars > 0:
            return (coins, dollars)
        
        return None
    
    @staticmethod
    def aggregate_costs(*cost_infos: CostInfo) -> CostInfo:
        """
        Aggregate multiple cost info objects.
        
        Args:
            *cost_infos: Variable number of CostInfo objects
            
        Returns:
            Aggregated CostInfo
        """
        total_coins = sum(c.coins_used for c in cost_infos)
        total_dollars = sum(c.dollars_used for c in cost_infos)
        operations = [c.operation for c in cost_infos if c.operation]
        
        return CostInfo(
            coins_used=total_coins,
            dollars_used=total_dollars,
            operation=", ".join(operations) if operations else "multiple operations"
        )


# Made with Bob