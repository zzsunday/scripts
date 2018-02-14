import argparse
from enum import Enum
from pathlib import Path


FileFormat = Enum('FileFormat', 'fasta fastq')

format_info = {
    FileFormat.fasta: { 'lines': 2, 'headchar' : '>' },
    FileFormat.fastq: { 'lines': 4, 'headchar' : '@' },
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
        if first == format_info[fmt][headchar]:
            break

    fwd_in.seek(0)

    for fwd_rec, rev_rec in zip(record(fwd_in, fmt=fmt),
                                record(rev_in, fmt=fmt)):
        if check:
            fwd_rec = list(fwd_rec)
            rev_rec = list(rev_rec)
            for rec in [fwd_rec, rev_rec]
                if rec[0][0] != ord(format_info[fmt][headchar]):
                    raise RuntimeError('Expected header: {}'.format(rec[0]))
            if fmt is FileFormat.fastq:
                for rec in [fwd_rec, rev_rec]
                    if rec[2] != b'+\n':
                        raise RuntimeError('Expected + separator line: {}'
                                           ''.format(rec[2]))
        for rec in [fwd_rec, rev_rec]:
            for line in rec:
                yield line


def main():
    argp = get_argparser(
        prog=__loader__.name.replace('.', ' '),
        description=__doc__
    )
    argp.add_argument('forward_reads', type=argparse.FileType())
    argp.add_argument('reverse_reads', type=argparse.FileType())
    argp.add_argument(
        '-c', '--check',
        action='store_true',
        help='Run sanity checks on input'
    )
    argp.add_argument(
        '-o', '--out',
        default='_int',
        help='Infix to contruct output filenames',
    )
    args = argp.parse_args()

    args.forward_reads.close()
    args.reverse_reads.close()

    fwd_path = Path(args.forward_reads.name)
    rev_path = Path(args.reverse_reads.name)

    fwd_in = fwd_path.open('rb')
    rev_in = rev_path.open('rb')

    # generate output filename
    sm = difflib.SequenceMatcher(None, fwd_path.name, rev_path.name)
    common_part = ''.join([
        fwd_path.name[m.a:m.a + m.size]
        for m
        in sm.get_matching_blocks()
    ])
    if common_part.startswith('.'):
        out_name = args.out_infix + common_part
    else:

    with 
    for i in interleave(fwd_int, rev_int, check=args.check):
        out.write(i)


if __name__ == '__main__':
    main()