import argparse
from enum import Enum
from pathlib import Path
import sys

from . import get_argparser


FileFormat = Enum('FileFormat', 'fasta fastq')

format_info = {
    FileFormat.fasta: {'lines': 2, 'headchar': '>'},
    FileFormat.fastq: {'lines': 4, 'headchar': '@'},
}


def record(file, fmt=FileFormat.fastq):
    """
    Given a fasta or fastq file return iterator over sequences

    Implements the grouper recipe from collections doc
    """
    args = [iter(file)] * format_info[fmt]['lines']
    return zip(*args)


def interleave(fwd_in, rev_in, check=False):
    """
    Interleave reads from two files
    """
    first = fwd_in.read(1)
    for fmt in FileFormat:
        if first == format_info[fmt]['headchar']:
            break

    fwd_in.seek(0)

    for fwd_rec, rev_rec in zip(record(fwd_in, fmt=fmt),
                                record(rev_in, fmt=fmt)):
        if check:
            fwd_rec = list(fwd_rec)
            rev_rec = list(rev_rec)
            for rec in [fwd_rec, rev_rec]:
                if rec[0][0] != ord(format_info[fmt]['headchar']):
                    raise RuntimeError('Expected header: {}'.format(rec[0]))
            if fmt is FileFormat.fastq:
                for rec in [fwd_rec, rev_rec]:
                    if rec[2] != b'+\n':
                        raise RuntimeError('Expected + separator line: {}'
                                           ''.format(rec[2]))
        for rec in [fwd_rec, rev_rec]:
            for line in rec:
                yield line


def main():
    argp = get_argparser(
        prog=__loader__.name.replace('.', ' '),
        description=__doc__,
        project_home=False,
        threads=False,
    )
    argp.add_argument('forward_reads', type=argparse.FileType())
    argp.add_argument('reverse_reads', type=argparse.FileType())
    argp.add_argument(
        '-c', '--check',
        action='store_true',
        help='Run sanity checks on input'
    )
    argp.add_argument(
        '-o', '--output',
        nargs='?',
        default=None,
        help='Path to output file.  If not provided output is written to '
             'stdout.',
    )
    args = argp.parse_args()

    args.forward_reads.close()
    args.reverse_reads.close()

    fwd_path = Path(args.forward_reads.name)
    rev_path = Path(args.reverse_reads.name)

    fwd_in = fwd_path.open('rb')
    rev_in = rev_path.open('rb')

    if args.output is None:
        out = sys.stdout.buffer
    else:
        try:
            out = Path(args.output).open('wb')
        except Exception as e:
            argp.error('Failed to open file for writing: {}: {}: {}'
                       ''.format(args.output, e.__class__.__name__, e))

    for i in interleave(fwd_in, rev_in, check=args.check):
        out.write(i)


if __name__ == '__main__':
    main()
