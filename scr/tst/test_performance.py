import unittest
from difflib import SequenceMatcher

import time

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from termcolor import colored

from fcn.processing import *

COPY_PASTE_SCORE = 0.3059463604477232
LAST_FITNESS_NAME = "last_fitness.txt"


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


class TestPerformance(unittest.TestCase):
    """Tests the performance of the system."""

    def test_speed(self):
        """Tests how much time it takes to run algorithm on 1 MB file."""
        start = time.time()
        process_file(Path("../data/test/blabot.txt"))
        end = time.time()
        print(colored('\n\nRun time: {0} seconds'.format(end-start), 'cyan'))

    def test_accuracy(self):
        """Tests the model accuracy."""
        process_file(Path("../data/train/ukazka_HDS.ortho.txt"))

        # Open ground truth output
        f = open("../data/train/ukazka_HDS.phntrn.txt", "r", encoding='utf-8')
        ground_truth = f.read()
        f.close()

        # Open predicted output
        f = open("../data/output/ukazka_HDS.phntrn.txt", "r", encoding='utf-8')
        predict = f.read()
        f.close()

        # Open previous predicted output
        f = open(LAST_FITNESS_NAME, "r", encoding='utf-8')
        last_fitness = float(f.read())
        f.close()

        # Compute the difference between outputs
        vect = TfidfVectorizer(min_df=1, encoding="utf-8", lowercase=False, token_pattern="(.)")
        tfidf = vect.fit_transform([ground_truth, predict])
        pairwise_similarity = tfidf * tfidf.T

        relative_fitness = np.min(pairwise_similarity)

        print(colored('\n\nRelative similarity on train data: {0}'.format(relative_fitness), 'cyan'))
        print(colored('Previous relative data similarity: {0}'.format(last_fitness), 'cyan'))
        print(colored('Relative similarity of copy-paste: {0}'.format(COPY_PASTE_SCORE), 'cyan'))

        with open("last_fitness.txt", 'w', encoding='utf-8') as f:
            f.write(str(relative_fitness))
