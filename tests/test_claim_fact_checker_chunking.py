import unittest
from unittest.mock import patch

from utils import claim_fact_checker


class ProcessSingleInteractorChunkingTest(unittest.TestCase):
    def test_preserves_all_functions_across_chunks(self):
        function_count = 25
        interactor = {
            'primary': 'TARGET',
            'functions': [
                {'function': f'Function {idx}', 'evidence': []}
                for idx in range(function_count)
            ],
        }

        batch_sizes = []

        def fake_call(main_protein, primary, claims_batch, api_key, recovery_hint=None):
            batch_sizes.append(len(claims_batch))
            return {
                'validations': [
                    {
                        'claim_number': idx + 1,
                        'function_name': claim.get('function'),
                        'validity': 'TRUE',
                        'validation_note': '',
                    }
                    for idx, claim in enumerate(claims_batch)
                ]
            }

        with patch('utils.claim_fact_checker.call_gemini_for_claim_validation', side_effect=fake_call):
            with patch('utils.claim_fact_checker.time.sleep', return_value=None):
                result = claim_fact_checker._process_single_interactor(
                    int_idx=1,
                    interactor=interactor,
                    main_protein='MAIN',
                    api_key='dummy',
                    total_interactors=1,
                    max_functions=20,
                )

        processed_interactor = result['interactor']
        self.assertEqual(len(processed_interactor['functions']), function_count)
        self.assertListEqual(
            [f['function'] for f in processed_interactor['functions']],
            [f'Function {idx}' for idx in range(function_count)],
        )
        self.assertEqual(result['stats']['claims'], function_count)
        self.assertEqual(batch_sizes, [20, 5])


if __name__ == '__main__':
    unittest.main()
