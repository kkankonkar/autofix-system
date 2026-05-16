"""Tests for cost tracking functionality."""
import pytest
from fixium.cost_tracker import CostTracker, CostInfo


class TestCostInfo:
    """Test CostInfo dataclass."""
    
    def test_default_values(self):
        """Test default initialization."""
        cost = CostInfo()
        assert cost.coins_used == 0.0
        assert cost.dollars_used == 0.0
        assert cost.operation == ""
    
    def test_custom_values(self):
        """Test custom initialization."""
        cost = CostInfo(coins_used=100.5, dollars_used=0.0123, operation="test")
        assert cost.coins_used == 100.5
        assert cost.dollars_used == 0.0123
        assert cost.operation == "test"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        cost = CostInfo(coins_used=50.0, dollars_used=0.005, operation="review")
        result = cost.to_dict()
        assert result == {
            'coins_used': 50.0,
            'dollars_used': 0.005,
            'operation': 'review'
        }
    
    def test_format_for_comment_with_costs(self):
        """Test formatting with costs."""
        cost = CostInfo(coins_used=123.45, dollars_used=0.0123, operation="test")
        result = cost.format_for_comment()
        assert "💰 Cost Information" in result
        assert "123.45 coins" in result
        assert "$0.0123" in result
    
    def test_format_for_comment_no_costs(self):
        """Test formatting with no costs."""
        cost = CostInfo()
        result = cost.format_for_comment()
        assert result == ""


class TestCostTracker:
    """Test CostTracker extraction logic."""
    
    def test_extract_costs_bob_tool_format(self):
        """Test Bob CLI tool cost format extraction."""
        output = "[using tool attempt_completion: Successfully completed | Cost: 0.02]"
        cost = CostTracker.extract_costs(output, "test")
        assert cost.coins_used == 0.02  # Bob reports in coins
        assert cost.dollars_used == 0.01  # 0.02 / 2 (Bob Pro: 2 coins = $1)
        assert cost.operation == "test"
    
    def test_extract_costs_multiple_bob_tools(self):
        """Test multiple Bob CLI tool costs."""
        output = """
        [using tool read_file: Success | Cost: 0.01]
        [using tool write_file: Success | Cost: 0.015]
        [using tool attempt_completion: Success | Cost: 0.02]
        """
        cost = CostTracker.extract_costs(output, "test")
        assert cost.coins_used == 0.045  # 0.01 + 0.015 + 0.02 (Bob reports in coins)
        assert cost.dollars_used == 0.0225  # 0.045 / 2 (Bob Pro: 2 coins = $1)
    
    def test_extract_costs_simple(self):
        """Test simple cost extraction (legacy format)."""
        output = "Used 100.5 coins, cost: $0.0105"
        cost = CostTracker.extract_costs(output, "test")
        assert cost.coins_used == 100.5
        assert cost.dollars_used == 0.0105
        assert cost.operation == "test"
    
    def test_extract_costs_summary_pattern(self):
        """Test cost summary pattern."""
        output = "Total cost: 250.75 bob coins ($0.0251)"
        cost = CostTracker.extract_costs(output, "review")
        assert cost.coins_used == 250.75
        assert cost.dollars_used == 0.0251
    
    def test_extract_costs_multiple_matches(self):
        """Test with multiple cost mentions (takes last)."""
        output = """
        Step 1: 50 coins used
        Step 2: 75 coins used
        Total: 125 coins used, $0.0125
        """
        cost = CostTracker.extract_costs(output)
        assert cost.coins_used == 125.0
        assert cost.dollars_used == 0.0125
    
    def test_extract_costs_no_match(self):
        """Test with no cost information."""
        output = "This is just regular output"
        cost = CostTracker.extract_costs(output)
        assert cost.coins_used == 0.0
        assert cost.dollars_used == 0.0
    
    def test_extract_costs_empty_output(self):
        """Test with empty output."""
        cost = CostTracker.extract_costs("")
        assert cost.coins_used == 0.0
        assert cost.dollars_used == 0.0
    
    def test_parse_bob_cost_line_valid(self):
        """Test parsing valid cost line."""
        line = "Cost: 123.45 coins ($0.0123)"
        result = CostTracker.parse_bob_cost_line(line)
        assert result is not None
        assert result[0] == 123.45
        assert result[1] == 0.0123
    
    def test_parse_bob_cost_line_invalid(self):
        """Test parsing non-cost line."""
        line = "This is just a regular line"
        result = CostTracker.parse_bob_cost_line(line)
        assert result is None
    
    def test_parse_bob_cost_line_partial(self):
        """Test parsing line with only coins."""
        line = "Used 50.5 coins"
        result = CostTracker.parse_bob_cost_line(line)
        assert result is not None
        assert result[0] == 50.5
        assert result[1] == 0.0
    
    def test_aggregate_costs_single(self):
        """Test aggregating single cost."""
        cost1 = CostInfo(coins_used=100.0, dollars_used=0.01, operation="op1")
        result = CostTracker.aggregate_costs(cost1)
        assert result.coins_used == 100.0
        assert result.dollars_used == 0.01
        assert "op1" in result.operation
    
    def test_aggregate_costs_multiple(self):
        """Test aggregating multiple costs."""
        cost1 = CostInfo(coins_used=100.0, dollars_used=0.01, operation="op1")
        cost2 = CostInfo(coins_used=50.0, dollars_used=0.005, operation="op2")
        cost3 = CostInfo(coins_used=25.5, dollars_used=0.0025, operation="op3")
        
        result = CostTracker.aggregate_costs(cost1, cost2, cost3)
        assert result.coins_used == 175.5
        assert result.dollars_used == 0.0175
        assert "op1" in result.operation
        assert "op2" in result.operation
        assert "op3" in result.operation
    
    def test_aggregate_costs_empty(self):
        """Test aggregating no costs."""
        result = CostTracker.aggregate_costs()
        assert result.coins_used == 0.0
        assert result.dollars_used == 0.0
    
    def test_extract_costs_case_insensitive(self):
        """Test case-insensitive extraction."""
        output = "USED 100 COINS, COST: $0.01"
        cost = CostTracker.extract_costs(output)
        assert cost.coins_used == 100.0
        assert cost.dollars_used == 0.01
    
    def test_extract_costs_with_bob_prefix(self):
        """Test extraction with 'bob' prefix."""
        output = "Total: 150.5 bob coins ($0.015)"
        cost = CostTracker.extract_costs(output)
        assert cost.coins_used == 150.5
        assert cost.dollars_used == 0.015


# Made with Bob