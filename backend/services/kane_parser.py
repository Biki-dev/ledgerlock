import json


def parse_kane_output(stdout: str):

    events = []

    steps = []

    run_end = None

    for line in stdout.splitlines():

        line = line.strip()

        if not line:
            continue

        try:

            event = json.loads(line)

        except json.JSONDecodeError:

            # Ignore non-JSON output.
            continue

        events.append(event)

        # Final event.

        if event.get("type") == "run_end":

            run_end = event

        # Run progress events have no type field.

        elif "step" in event:

            steps.append(event)

    return {

        "events": events,

        "steps": steps,

        "run_end": run_end
    }