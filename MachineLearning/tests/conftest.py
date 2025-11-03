"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
def calculate_sum(numbers):
    """Calculate the sum of a list of numbers.

    Args:
        numbers: List of numbers to sum

    Returns:
        The sum of all numbers
    """
    total = 0
    for num in numbers:
        total += num
    return total


class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, value):
        """Add a value to the result."""
        self.result += value
        return self.result

    def subtract(self, value):
        """Subtract a value from the result."""
        self.result -= value
        return self.result
'''


@pytest.fixture
def sample_javascript_code():
    """Sample JavaScript code for testing."""
    return '''
function reverseString(str) {
    /**
     * Reverse a string
     * @param {string} str - The string to reverse
     * @returns {string} The reversed string
     */
    return str.split('').reverse().join('');
}

class Stack {
    /**
     * Simple stack implementation
     */
    constructor() {
        this.items = [];
    }

    push(element) {
        this.items.push(element);
    }

    pop() {
        if (this.items.length === 0) {
            return null;
        }
        return this.items.pop();
    }
}
'''


@pytest.fixture
def sample_bad_code():
    """Sample low-quality code for testing."""
    return '''
def foo():
    # TODO: implement this later
    pass

def x():
    return 1
'''
