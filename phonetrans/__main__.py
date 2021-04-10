"""Project main script"""
import argparse

from fcn.processing import process_file

parser = argparse.ArgumentParser()
parser.add_argument('input', metavar='INPUT', type=str, help='Input file with written czech text')
parser.add_argument('output', metavar='OUTPUT', nargs='?', type=str, const=None,
                    help='Output file to save phonetic transcription')

if __name__ == '__main__':
    args = parser.parse_args()
    process_file(args.input, args.output)
