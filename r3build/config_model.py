from typing import Dict, List, Union


sections = {
    "event": {
        "__description__": "`event` section defines how r3build handle events.",
        "__type__": dict,
        "ignore_events_while_run": {
            "required": False,
            "type": bool,
            "default": True,
            "description": "Ignore events occurred while a processor is running.\nDisabling this flag may result in a never-ending execution loop. Disable with care.",
        },
        "rate_limit_duration": {
            "required": False,
            "type": float,
            "default": 0.01,
            "description": "Duration for dropping (debouncing) events that occurred so closely (the unit is second).",
        },
    },
    "log": {
        "__description__": "`log` section defines what r3build will output.",
        "__type__": dict,
        "accepted_events": {
            "required": False,
            "type": bool,
            "default": False,
            "description": "Show all incoming events except rate-limited ones.",
        },
        "all": {
            "required": False,
            "type": bool,
            "default": False,
            "description": "Turn on all event logs.\nNotice: it overrides all other log flags.",
        },
        "dispatched_events": {
            "required": False,
            "type": bool,
            "default": False,
            "description": "Show events dispatched to processors.",
        },
        "filtered_events": {
            "required": False,
            "type": bool,
            "default": False,
            "description": "Show filtered events.",
        },
        "processor_output": {
            "required": False,
            "type": bool,
            "default": True,
            "description": "Show the output of the executed processor.",
        },
        "rate_limited_events": {
            "required": False,
            "type": bool,
            "default": False,
            "description": "Show rate-limited events.\nHint: rate-limit duration is set by `event.rate_limit_duration`.",
        },
        "result": {
            "required": False,
            "type": bool,
            "default": True,
            "description": "Show if the run was successful or not.",
        },
        "time": {
            "required": False,
            "type": bool,
            "default": True,
            "description": "Show target's execution time.",
        },
    },
}


processors = {
    "command": {
        "__description__": "`command` processor invokes a command.",
        "__type__": dict,
        "command": {
            "required": True,
            "type": str,
            "default": "",
            "description": "The command to run. This command will be executed by `subprocess.run` with `shell=True`.",
        },
        "environment": {
            "required": False,
            "type": Dict[str, str],
            "default": "",
            "description": "Specify additional environment variables.\nBy default, r3build inherits the parent's envs.",
        },
    },
    "common": {
        "__description__": "`target` array-of-tables defines jobs.\n - What to watch (match and exclude files with glob and regex)\n - What processor to execute\n - How the processor process things\n... and etc.",
        "__type__": list,
        "glob": {
            "required": False,
            "type": Union[List[str], str],
            "default": "",
            "description": "One or more glob patterns to match the file path.\nThe target will be triggered if one or more patterns match to it.",
        },
        "glob_exclude": {
            "required": False,
            "type": Union[List[str], str],
            "default": "",
            "description": "One or more glob patterns to exclude. The effect is opposite to `glob`.\nThe target won't be triggered if one or more patterns match to it.",
        },
        "name": {
            "required": False,
            "type": str,
            "default": "noname",
            "description": "Human-readable name of the target.",
        },
        "path": {
            "required": False,
            "type": str,
            "default": ".",
            "description": "The root directory to watch.\nAny file events (move, delete, create, modify) inside this directory will be reported to r3build recursively.",
        },
        "processor": {
            "required": True,
            "type": str,
            "default": "",
            "description": "The ID of the processor for the target.\nTo see the full list of processors, run `python -m r3build --processors`.\nFor processor-specific configs, see the following sections.",
        },
        "regex": {
            "required": False,
            "type": Union[List[str], str],
            "default": "",
            "description": "One or more regular expression patterns to match the file path.\nThe target will be triggered if one or more patterns match to it.",
        },
        "regex_exclude": {
            "required": False,
            "type": Union[List[str], str],
            "default": "",
            "description": "One or more regular expression patterns to exclude. The effect is opposite to `regex`.\nThe target won't be triggered if one or more file patterns match to it.",
        },
        "when": {
            "required": False,
            "type": Union[List[str], str],
            "default": "",
            "description": 'One or more types of events to trigger this job.\nThe job will accept all types of events if it\'s ommitted.\nAvailable choices are "moved", "deleted", "created", "modified".',
        },
    },
    "make": {
        "__description__": "`make` processor runs a target in a Makefile.",
        "__type__": dict,
        "directory": {
            "required": False,
            "type": str,
            "default": "",
            "description": "The directory to read Makefile in. Equivalent to `make -C` option.",
        },
        "environment": {
            "required": False,
            "type": Dict[str, str],
            "default": "",
            "description": "Specify additional environment variables.\nBy default, r3build inherits the parent's envs.",
        },
        "jobs": {
            "required": False,
            "type": int,
            "default": 0,
            "description": "Number of parallel jobs. Equivalent to `make -j` option.\nIf it's zero, r3build will decide N of jobs with multiprocessing.cpu_count().",
        },
        "target": {
            "required": False,
            "type": str,
            "default": "",
            "description": "The make target.",
        },
    },
    "pytest": {
        "__description__": "`pytest` processor runs pytest on a package (directory) or a module (file).",
        "__type__": dict,
        "target": {
            "required": True,
            "type": str,
            "default": "",
            "description": "File or directory to run tests.\nThis string is passed to pytest.main() and also used for reloading Python modules to update test code.\nFor an advanced use like passing arbitrary arguments to pytest, please use `command` processor.",
        },
    },
}
