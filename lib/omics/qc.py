"""
Run QC on metagenomic reads from multiple samples
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess
import sys

from omics import get_argparser, DEFAULT_THREADS, DEFAULT_VERBOSITY


def qc_sample(path, *, clean_only=False, adapters=None, keep_all=False,
              no_dereplicate=False, no_fasta_interleave=False,
              verbosity=DEFAULT_VERBOSITY, scythe_sickle=False,
              threads=DEFAULT_THREADS, project=None):
    """
    Do QC for a single sample

    This is a wrapper for the omics-qc-sample script
    """
    script = 'omics-qc-sample'

    args = []
    not clean_only or args.append('--clean-only')
    not keep_all or args.append('--keep-all')
    if adapters:
        args += ['--adapters', adapters]
    not no_dereplicate or args.append('--no-dereplicate')
    not no_interleave or args.append('--no-interleave')
    not no_fasta_interleave or args.append('--no-fasta-interleave')
    not scythe_sickle or args.append('--scythe-sickle')
    if threads is not None:
        args += ['--threads', str(threads)]
    if verbosity > DEFAULT_VERBOSITY:
        args.append('--verbosity={}'.format(verbosity))
        print('[qc] Calling qc-sample with arguments: {}'.format(args))

    p = subprocess.run(
        [script] + args,
        cwd=str(path),
    )
    if p.check_returncode():
        raise RuntimeError('Failed to run qc-sample: sample: {}: exit status: '
                           '{}'.format(path, p.returncode))


def qc(samples, *, clean_only=False, adapters=None, keep_all=False,
       no_dereplicate=False, no_interleave=False,
       no_fasta_interleave=False, verbosity=DEFAULT_VERBOSITY,
       scythe_sickle=False,
       threads=DEFAULT_THREADS, project=None):
    """
    Do quality control on multiple samples

    :param samples: List of pathlib.Path containing read data, one per sample
    :param kwargs: Options, see omics.qc.main for argsparse options.
    """
    # number of workers: how many samples are processed in parallel
    # HOWTO distribute CPUs among workers:
    #   1. allow at most (hard-coded) 6 workers
    #   2. # of workers is the least of 6, # of CPUs, and # of samples
    #   3. # of CPUs/worker at least 1
    MAX_WORKERS = 6
    num_workers = min(MAX_WORKERS, len(samples), threads)
    threads_per_worker = max(1, int(threads / num_workers))

    if verbosity > DEFAULT_VERBOSITY:
        print('[qc] Processing {} samples in parallel, using {} threads each'
              ''.format(num_workers, threads_per_worker))

    errors = []

    with ThreadPoolExecutor(max_workers=num_workers) as e:
        futures = {}
        for path in samples:
            futures[e.submit(
                qc_sample,
                path,
                clean_only=clean_only,
                adapters=adapters,
                keep_all=keep_all,
                no_dereplicate=no_dereplicate,
                no_interleave=no_interleave,
                no_fasta_interleave=no_fasta_interleave,
                scythe_sickle=scythe_sickle,
                verbosity=verbosity,
                project=project,
                threads=threads_per_worker,
            )] = path

        for fut in as_completed(futures.keys()):
            sample_path = futures[fut]
            e = fut.exception()
            if e is None:
                if verbosity >= DEFAULT_VERBOSITY + 2:
                    print('Done: {}'.format(sample_path.name))
            else:
                errors.append(
                    '[qc] (error): {}: {}: {}'
                    ''.format(sample_path, e.__class__.__name__, e)
                )

    if errors:
        raise(RuntimeError('\n'.join(errors)))


def main():
    argp = get_argparser(
        prog=__loader__.name.replace('.', ' '),
        description=__doc__,
    )
    argp.add_argument(
        'samples',
        nargs='*',
        default=['.'],
        help='List of directories, one per sample that contain the sample\'s '
             'reads. The default is to take the current directory and '
             'process a single sample.  The names of the reads files must be '
             'fwd.fastq and rev.fastq, currently this can not be set manually.'
             ' Use the omics-qc-sample script directly to specify filenames, '
             'omics-qc is just a wrapper after all.'
    )
    argp.add_argument(
        '--clean-only',
        action='store_true',
        help='Remove all files made by a previously run of qc and exit.',
    )
    argp.add_argument(
        '-a', '--adapters',
        metavar='FILE',
        help='Specify the adapters file used in the adpater trimming step.  By'
             ' default the Illumina adapter file TruSeq3-PE-2.fa as '
             'distributed by the Trimmomatic project will be used.',
    )
    argp.add_argument(
        '--keep-all',
        action='store_true',
        help='Keep all intermediate files, by default some not-so-important '
             'intermediate results will be deleted to save disk space.',
    )
    argp.add_argument(
        '--no-dereplicate',
        action='store_true',
        help='Option to skip the de-replication step',
    )
    argp.add_argument(
        '--no-interleave',
        action='store_true',
        help='Option to skip building the interleaved reads file',
    )
    argp.add_argument(
        '--no-fasta-interleave',
        action='store_true',
        help='Skip building the interleaved fasta file, interleaved fastq '
             'files will still be build.',
    )
    argp.add_argument(
        '-S', '--scythe-sickle',
        action='store_true',
        help='Use scythe + sickle instead of (the default) Trimmomatic',
    )
    args = argp.parse_args()
    args.samples = [Path(i) for i in args.samples]
    for i in args.samples:
        if not i.is_dir():
            argp.error('Directory not found: {}'.format(i))

    try:
        qc(
            args.samples,
            clean_only=args.clean_only,
            adapters=args.adapters,
            keep_all=args.keep_all,
            no_dereplicate=args.no_dereplicate,
            no_interleave=args.no_interleave,
            no_fasta_interleave=args.no_fasta_interleave,
            scythe_sickle=args.scythe_sickle,
            verbosity=args.verbosity,
            threads=args.threads,
            project=args.project,
        )
    except Exception as e:
        if args.traceback:
            raise
        else:
            print('[qc] (error) {}: {}'.format(e.__class__.__name__, e),
                  file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
