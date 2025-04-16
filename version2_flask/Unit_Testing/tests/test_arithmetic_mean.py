# Import the pytest function

# We import the function
from functions.arithmetic_mean import arithmetic_mean


def test_all_ones():
    assert arithmetic_mean([1, 1, 1, 1]) == 1
