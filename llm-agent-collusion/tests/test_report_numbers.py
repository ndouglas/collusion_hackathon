from src.continuous_double_auction.evaluation.report_numbers import fisher_p, mde, permutation_p


def test_permutation_p_is_large_for_identical_groups_and_small_for_separated_ones():
    assert permutation_p([1.0, 2.0, 3.0] * 4, [1.0, 2.0, 3.0] * 4, n_perm=2000) > 0.9
    assert permutation_p([10.0 + i * 0.01 for i in range(10)], [0.0 + i * 0.01 for i in range(10)], n_perm=2000) < 0.001


def test_fisher_p_matches_a_known_table():
    # 3/3 vs. 0/3: two-sided Fisher exact p = 0.1
    assert abs(fisher_p(3, 3, 0, 3) - 0.1) < 1e-9


def test_mde_shrinks_with_more_runs():
    small = mde([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0])
    large = mde([1.0, 2.0, 3.0, 4.0] * 4, [1.0, 2.0, 3.0, 4.0] * 4)
    assert large < small
