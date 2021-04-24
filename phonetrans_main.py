"""Project main script"""
import argparse

from phonetrans.fcn.processing import transcribe_file

parser = argparse.ArgumentParser()
parser.add_argument('input', metavar='INPUT', type=str, help='Input file with written czech text')
parser.add_argument('output', metavar='OUTPUT', nargs='?', type=str, const=None,
                    help='Output file to save phonetic transcription')

if __name__ == '__main__':
    args = parser.parse_args()
    transcribe_file(args.input, args.output)