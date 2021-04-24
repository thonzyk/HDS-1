"""Project main script"""
import argparse
import os
from pathlib import Path

from phonetrans.fcn.processing import transcribe_file
from unitselection.fcn.concate import synthetize_speech
from unitselection.fcn.constants import *
from unitselection.fcn.inventory_diphone import inventory_create

parser = argparse.ArgumentParser()
parser.add_argument('input', metavar='INPUT', type=str, help='Input file with written czech text')
parser.add_argument('hds_data_dir', metavar='HDS_DATA_DIR', type=str, help='HDS data directory')
parser.add_argument('output_dir', metavar='OUTPUT_DIR', type=str, help='Directory for output .wav files')

if __name__ == '__main__':
    # Load params
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # Prepare inventory
    hds_dir = Path(args.hds_data_dir)
    if not os.path.exists(hds_dir / PREP / INV) or not os.path.exists(hds_dir / PREP / PHON_SIM):
        inventory_create(hds_dir)

    # Transcribe input text
    input_file = Path(args.input)
    trans_file = input_file.parent / "trans.txt"
    transcribe_file(input_file, trans_file)

    # Synthesize voice signal and save to out directory
    hds_dir = Path(args.hds_data_dir)
    synthetize_speech(trans_file, hds_dir, out_dir)
