import random
from typing import List
from pprint import pprint

MINIMUM_DIMENSION_SIZE = 10
MAXIMUM_DIMENSION_SIZE = 20

TYPE_ANNOTATION_MATRIX = List[List[int]]


def get_random_integer_within_range(max_dim_count: int, min_dim_count: int):
    if max_dim_count < min_dim_count:
        raise ValueError("Maximum dimension count should be no less than maximum dimension count")
    number_of_dimensions = random.randint(min_dim_count, max_dim_count)
    return number_of_dimensions


def generate_random_binary_matrix(
        min_dim_count: int = MINIMUM_DIMENSION_SIZE,
        max_dim_count: int = MAXIMUM_DIMENSION_SIZE
) -> TYPE_ANNOTATION_MATRIX:
    """
    Generate a 2D square matrix randomly filled with 0s and 1s with a random dimension size from min_row to max_row
    :param min_dim_count: minimum size of the matrix
    :param max_dim_count: maximum size of the matrix
    :return: a 2D matrix
    """
    number_of_dimensions = get_random_integer_within_range(max_dim_count, min_dim_count)
    matrix = [
        [random.randint(0, 1) for _ in range(number_of_dimensions)] for _ in range(number_of_dimensions)
    ]
    return matrix


def sort_matrix_rows_builtin(matrix: TYPE_ANNOTATION_MATRIX, reverse=False) -> TYPE_ANNOTATION_MATRIX:
    """
    Use built in sort  method to sort the rows of a matrix
    :param matrix: matrix to sort the rows
    :param reverse: sort direction reversing flag
    :return: sorted matrix
    """
    for row in matrix:
        row.sort(reverse=reverse)
    return matrix


def sort_matrix_rows_by_counting(matrix: TYPE_ANNOTATION_MATRIX) -> TYPE_ANNOTATION_MATRIX:
    """
    Count the number of 1's and 0's in each row and create a new sorted row.
    Return the collection of the new generated rows
    :param matrix:matrix to sort the rows
    :return:
    """
    sorted_matrix = []
    for row in matrix:
        one_count = sum(row)
        zero_count = len(row) - one_count
        new_row = [0] * zero_count + [1] * one_count
        sorted_matrix.append(new_row)
    return sorted_matrix


def main():
    matrix = generate_random_binary_matrix()
    print("Initial matrix")
    pprint(matrix)

    count_sorted = sort_matrix_rows_by_counting(matrix=matrix)
    print("Count sorted")
    pprint(count_sorted)


if __name__ == "__main__":
    main()
