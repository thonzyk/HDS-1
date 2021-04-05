"""Project performance tests"""
import time
import unittest

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from termcolor import colored

from fcn.processing import *

COPY_PASTE_SCORE = 0.3059463604477232
LAST_FITNESS_NAME = "last_fitness.txt"


class TestPerformance(unittest.TestCase):
    """Tests the performance of the system."""

    def test_speed(self, numb_of_reps=10):
        """Tests how much time it takes on average to run algorithm on 1 MB file."""

        avg_time = 0.0

        for i in range(numb_of_reps):
            start = time.time()
            process_file(Path("../data/test/blabot.txt"))
            end = time.time()

            avg_time += end - start

        avg_time /= numb_of_reps

        print(colored('\n\nExecute time: {0} seconds'.format(avg_time), 'cyan'))

    def test_accuracy(self):
        """Tests the algorithm accuracy."""
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
