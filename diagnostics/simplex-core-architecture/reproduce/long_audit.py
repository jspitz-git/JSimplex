"""Post-exit audit; incomplete output never becomes a successful reference."""
import argparse
import json
from pathlib import Path
import tomllib


def audit(process, report, windows):
    process, report = process or {}, report or {}
    result = report.get('result', {})
    windows = windows or []
    labels = report.get('counter_labels', [])
    totals = [0] * len(labels)
    complete_counters = bool(windows and labels)
    phase_two_steps = 0
    phase_two_seconds = 0.0
    accepted_steps = 0
    for window in windows:
        deltas = window.get('counter_deltas', [])
        if len(deltas) != len(labels):
            complete_counters = False
        else:
            totals = [a + b for a, b in zip(totals, deltas)]
        steps = window.get('accepted_steps', 0)
        accepted_steps += steps
        if window.get('phase') == 'phase_two':
            phase_two_steps += steps
            phase_two_seconds += window.get('seconds', 0.0)
    complete_counters = complete_counters and dict(zip(labels, totals)) == result.get('counts')
    complete_sequence = bool(windows and windows[-1].get('reason') == 'final_partial'
                             and len(windows) == result.get('recorder_tail', {}).get('windows'))
    normal_exit = process.get('reason') == 'exit0' and process.get('returncode') == 0
    certified_result = (report.get('solver_returned') is True and result.get('status') == 'OPTIMAL'
                        and result.get('original_primal_feasible') is True)
    certificate_observed = result.get('counts', {}).get('_original_optimality_certified', 0) > 0
    success = (report.get('mode') == 'counted' and normal_exit and process.get('pins_unchanged') is True
               and certified_result and certificate_observed and complete_counters and complete_sequence
               and phase_two_steps > 0 and phase_two_seconds > 0)
    return dict(chronology_reference_success=bool(success), normal_exit=normal_exit,
                pins_unchanged=process.get('pins_unchanged', False),
                certified_solver_result=certified_result,
                certificate_call_observed=certificate_observed,
                complete_counter_windows=complete_counters, complete_window_sequence=complete_sequence,
                phase_two_steps=phase_two_steps, phase_two_seconds=phase_two_seconds,
                accepted_steps=accepted_steps, windows=len(windows),
                status=result.get('status', 'NO_FINAL_RESULT'), reason=process.get('reason', 'NO_PROCESS_REPORT'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    parser.add_argument('--report', default='reference.toml')
    args = parser.parse_args()
    errors = []
    def read(path, loader):
        try:
            return loader(path.read_text())
        except (OSError, ValueError) as exc:
            errors.append(f'{path.name}: {exc}')
            return None
    process = read(args.attempt / 'process.json', json.loads)
    report_path = args.attempt / args.report
    report = read(report_path, tomllib.loads)
    raw_windows = read(Path(str(report_path) + '.windows.toml'), tomllib.loads)
    result = audit(process, report, None if raw_windows is None else raw_windows.get('windows'))
    result['read_errors'] = errors
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
