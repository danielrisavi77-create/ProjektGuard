import argparse
from pathlib import Path
from projektguard.benchmark.evidence_evaluator import evaluate_manifest


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--json-output')
    args=parser.parse_args(argv)
    _,summary=evaluate_manifest(Path(args.manifest))
    print('ProjektGuard Evidence Integrity Benchmark')
    print(f'Tests: {summary.total}')
    print(f'Passed: {summary.passed}')
    print(f'Pass rate: {summary.pass_rate:.2%}')
    print(f'UNKNOWN discipline: {summary.unknown_discipline:.2%}')
    print(f'Source-required cases: {summary.source_required_cases}')
    print(f'HIGH/CRITICAL source completeness: {summary.high_critical_source_completeness:.2%}')
    if args.json_output: Path(args.json_output).write_text(summary.model_dump_json(indent=2),encoding='utf-8')
    ok=summary.pass_rate>=.98 and summary.critical_false_positives==0 and summary.unknown_discipline>=.95 and summary.high_critical_source_completeness==1
    return 0 if ok else 1

if __name__=='__main__': raise SystemExit(main())
