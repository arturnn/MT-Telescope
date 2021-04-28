import unittest
from telescope.testset import PairwiseTestset


class TestTestset(unittest.TestCase):
    
    testset = PairwiseTestset(
        src=['Bonjour le monde.', "C'est un test."],
        system_x=['Greetings world', 'This is an experiment.'],
        system_y=['Hi world.', 'This is a Test.'],
        ref=['Hello world.', 'This is a test.'],
        language_pair="en-fr",
        filenames=["src.txt", "google.txt", "unbabel.txt", "ref.txt"]
    )

    def test_length(self):
        self.assertEqual(len(self.testset), 2)

    def test_get_item(self):
        expected = (
            'Bonjour le monde.',
            'Greetings world',
            'Hi world.',
            'Hello world.'
        )
        self.assertTupleEqual(expected, self.testset[0])
    