import unittest

from experiments.compare_experiment import measure


class CompareExperimentTests(unittest.TestCase):
    def test_measurement_uses_matching_loads_and_theory_for_both_tables(self):
        results = measure(capacity=101, load_factors=(0.2, 0.5))

        self.assertEqual(len(results), 2)
        for result, load_factor in zip(results, (0.2, 0.5)):
            self.assertAlmostEqual(result.load_factor, load_factor, places=2)
            self.assertEqual(result.item_count, round(load_factor * 101))
            self.assertAlmostEqual(
                result.chaining_success_theory, 1 + result.load_factor / 2
            )
            self.assertAlmostEqual(
                result.chaining_unsuccessful_theory, result.load_factor
            )
            self.assertAlmostEqual(
                result.linear_success_theory,
                0.5 * (1 + 1 / (1 - result.load_factor)),
            )
            self.assertAlmostEqual(
                result.linear_unsuccessful_theory,
                0.5 * (1 + 1 / (1 - result.load_factor) ** 2),
            )
            self.assertGreater(result.chaining_success_measured, 0)
            self.assertGreater(result.linear_success_measured, 0)


if __name__ == "__main__":
    unittest.main()
