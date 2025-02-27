from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from glob import glob

from invoke import Exit, task

from tasks.build_tags import compute_build_tags_for_flavor
from tasks.devcontainer import run_on_devcontainer
from tasks.flavor import AgentFlavor
from tasks.go import run_golangci_lint
from tasks.libs.ciproviders.github_api import GithubAPI
from tasks.libs.ciproviders.gitlab_api import (
    generate_gitlab_full_configuration,
    get_all_gitlab_ci_configurations,
    get_gitlab_ci_configuration,
    get_gitlab_repo,
    get_preset_contexts,
    load_context,
    read_includes,
    retrieve_all_paths,
)
from tasks.libs.common.check_tools_version import check_tools_version
from tasks.libs.common.color import Color, color_message
from tasks.libs.common.constants import DEFAULT_BRANCH, GITHUB_REPO_NAME
from tasks.libs.common.git import get_staged_files
from tasks.libs.common.utils import gitlab_section, is_pr_context, running_in_ci
from tasks.libs.types.copyright import CopyrightLinter, LintFailure
from tasks.modules import GoModule
from tasks.test_core import ModuleLintResult, process_input_args, process_module_results, test_core
from tasks.update_go import _update_go_mods, _update_references


@task
def python(ctx):
    """
    Lints Python files.
    See 'setup.cfg' and 'pyproject.toml' file for configuration.
    If running locally, you probably want to use the pre-commit instead.
    """

    print(
        f"""Remember to set up pre-commit to lint your files before committing:
    https://github.com/DataDog/datadog-agent/blob/{DEFAULT_BRANCH}/docs/dev/agent_dev_env.md#pre-commit-hooks"""
    )

    if running_in_ci():
        # We want to the CI to fail if there are any issues
        ctx.run("ruff format --check .")
        ctx.run("ruff check .")
    else:
        # Otherwise we just need to format the files
        ctx.run("ruff format .")
        ctx.run("ruff check --fix .")

    ctx.run("vulture")
    ctx.run("mypy")


@task
def copyrights(ctx, fix=False, dry_run=False, debug=False, only_staged_files=False):
    """
    Checks that all Go files contain the appropriate copyright header. If '--fix'
    is provided as an option, it will try to fix problems as it finds them. If
    '--dry_run' is provided when fixing, no changes to the files will be applied.
    """
    files = None

    if only_staged_files:
        staged_files = get_staged_files(ctx)
        files = [path for path in staged_files if path.endswith(".go")]

    try:
        CopyrightLinter(debug=debug).assert_compliance(fix=fix, dry_run=dry_run, files=files)
    except LintFailure:
        # the linter prints useful messages on its own, so no need to print the exception
        sys.exit(1)


@task
def filenames(ctx):
    """
    Scan files to ensure there are no filenames too long or containing illegal characters
    """
    files = ctx.run("git ls-files -z", hide=True).stdout.split("\0")
    failure = False

    if sys.platform == 'win32':
        print("Running on windows, no need to check filenames for illegal characters")
    else:
        print("Checking filenames for illegal characters")
        forbidden_chars = '<>:"\\|?*'
        for filename in files:
            if any(char in filename for char in forbidden_chars):
                print(f"Error: Found illegal character in path {filename}")
                failure = True

    print("Checking filename length")
    # Approximated length of the prefix of the repo during the windows release build
    prefix_length = 160
    # Maximum length supported by the win32 API
    max_length = 255
    for filename in files:
        if (
            not filename.startswith(
                ('test/kitchen/', 'tools/windows/DatadogAgentInstaller', 'test/workload-checks', 'test/regression')
            )
            and prefix_length + len(filename) > max_length
        ):
            print(
                f"Error: path {filename} is too long ({prefix_length + len(filename) - max_length} characters too many)"
            )
            failure = True

    if failure:
        raise Exit(code=1)


@task(iterable=['flavors'])
@run_on_devcontainer
def go(
    ctx,
    module=None,
    targets=None,
    flavor=None,
    build="lint",
    build_tags=None,
    build_include=None,
    build_exclude=None,
    rtloader_root=None,
    cpus=None,
    timeout: int | None = None,
    golangci_lint_kwargs="",
    headless_mode=False,
    include_sds=False,
    only_modified_packages=False,
    verbose=False,
    run_on=None,  # noqa: U100, F841. Used by the run_on_devcontainer decorator
):
    """
    Run go linters on the given module and targets.

    A module should be provided as the path to one of the go modules in the repository.

    Targets should be provided as a comma-separated list of relative paths within the given module.
    If targets are provided but no module is set, the main module (".") is used.

    If no module or target is set the tests are run against all modules and targets.

    --timeout is the number of minutes after which the linter should time out.
    --headless-mode allows you to output the result in a single json file.

    Example invokation:
        inv linter.go --targets=./pkg/collector/check,./pkg/aggregator
        inv linter.go --module=.
    """
    if not check_tools_version(ctx, ['golangci-lint']):
        print(
            color_message(
                "Error: The golanci-lint version you are using is not the correct one. Please run inv -e install-tools to install the correct version.",
                "red",
            )
        )
        raise Exit(code=1)

    if not check_tools_version(ctx, ['go']):
        print("Warning: If you have linter errors it might be due to version mismatches.", file=sys.stderr)

    modules, flavor = process_input_args(
        ctx,
        module,
        targets,
        flavor,
        headless_mode,
        build_tags=build_tags,
        only_modified_packages=only_modified_packages,
        lint=True,
    )

    lint_results, execution_times = run_lint_go(
        ctx=ctx,
        modules=modules,
        flavor=flavor,
        build=build,
        build_tags=build_tags,
        build_include=build_include,
        build_exclude=build_exclude,
        rtloader_root=rtloader_root,
        cpus=cpus,
        timeout=timeout,
        golangci_lint_kwargs=golangci_lint_kwargs,
        headless_mode=headless_mode,
        include_sds=include_sds,
        verbose=verbose,
    )

    if not headless_mode:
        with gitlab_section('Linter execution time'):
            print(color_message('Execution time summary:', 'bold'))
            for e in execution_times:
                print(f'- {e.name}: {e.duration:.1f}s')

    with gitlab_section('Linter failures'):
        success = process_module_results(flavor=flavor, module_results=lint_results)

    if success:
        if not headless_mode:
            print(color_message("All linters passed", "green"))
    else:
        # Exit if any of the modules failed on any phase
        raise Exit(code=1)


def run_lint_go(
    ctx,
    modules=None,
    flavor=None,
    build="lint",
    build_tags=None,
    build_include=None,
    build_exclude=None,
    rtloader_root=None,
    cpus=None,
    timeout=None,
    golangci_lint_kwargs="",
    headless_mode=False,
    include_sds=False,
    verbose=False,
):
    linter_tags = build_tags or compute_build_tags_for_flavor(
        flavor=flavor,
        build=build,
        build_include=build_include,
        build_exclude=build_exclude,
        include_sds=include_sds,
    )

    lint_results, execution_times = lint_flavor(
        ctx,
        modules=modules,
        flavor=flavor,
        build_tags=linter_tags,
        rtloader_root=rtloader_root,
        concurrency=cpus,
        timeout=timeout,
        golangci_lint_kwargs=golangci_lint_kwargs,
        headless_mode=headless_mode,
        verbose=verbose,
    )

    return lint_results, execution_times


def lint_flavor(
    ctx,
    modules: list[GoModule],
    flavor: AgentFlavor,
    build_tags: list[str],
    rtloader_root: bool,
    concurrency: int,
    timeout=None,
    golangci_lint_kwargs: str = "",
    headless_mode: bool = False,
    verbose: bool = False,
):
    """
    Runs linters for given flavor, build tags, and modules.
    """

    execution_times = []

    def command(module_results, module: GoModule, module_result):
        nonlocal execution_times

        with ctx.cd(module.full_path()):
            lint_results, time_results = run_golangci_lint(
                ctx,
                module_path=module.path,
                targets=module.lint_targets,
                rtloader_root=rtloader_root,
                build_tags=build_tags,
                concurrency=concurrency,
                timeout=timeout,
                golangci_lint_kwargs=golangci_lint_kwargs,
                headless_mode=headless_mode,
                verbose=verbose,
            )
            execution_times.extend(time_results)
            for lint_result in lint_results:
                module_result.lint_outputs.append(lint_result)
                if lint_result.exited != 0:
                    module_result.failed = True
        module_results.append(module_result)

    return test_core(
        modules, flavor, ModuleLintResult, "golangci_lint", command, headless_mode=headless_mode
    ), execution_times


@task
def list_ssm_parameters(_):
    """
    List all SSM parameters used in the datadog-agent repository.
    """

    ssm_owner = re.compile(r"^[A-Z].*_SSM_(NAME|KEY): (?P<param>[^ ]+) +# +(?P<owner>.+)$")
    ssm_params = defaultdict(list)
    with open(".gitlab-ci.yml") as f:
        for line in f:
            m = ssm_owner.match(line.strip())
            if m:
                ssm_params[m.group("owner")].append(m.group("param"))
    for owner in ssm_params.keys():
        print(f"Owner:{owner}")
        for param in ssm_params[owner]:
            print(f"  - {param}")


@task
def ssm_parameters(ctx, mode="all", folders=None):
    """
    Lint SSM parameters in the datadog-agent repository.
    """
    modes = ["env", "wrapper", "all"]
    if mode not in modes:
        raise Exit(f"Invalid mode: {mode}. Must be one of {modes}")
    if folders is None:
        lint_folders = [".circleci", ".github", ".gitlab", "test"]
    else:
        lint_folders = folders.split(",")
    repo_files = ctx.run("git ls-files", hide="both")
    error_files = []
    for filename in repo_files.stdout.split("\n"):
        if any(filename.startswith(f) for f in lint_folders):
            calls = list_get_parameter_calls(filename)
            if calls:
                error_files.extend(calls)
    if mode == "env":
        error_files = [f for f in error_files if not f.with_env_var]
    elif mode == "wrapper":
        error_files = [f for f in error_files if not f.with_wrapper]
    if error_files:
        print(
            f"[{color_message('ERROR', Color.RED)}] The following files contain unexpected syntax for aws ssm get-parameter:"
        )
        for filename in error_files:
            print(f"  - {filename}")
        raise Exit(code=1)
    print(f"[{color_message('OK', Color.GREEN)}] All files are correctly using wrapper for secret parameters.")


class SSMParameterCall:
    def __init__(self, file, line_nb, with_wrapper=False, with_env_var=False):
        """
        Initialize an SSMParameterCall instance.

        Args:
            file (str): The name of the file where the SSM parameter call is located.
            line_nb (int): The line number in the file where the SSM parameter call is located.
            with_wrapper (bool, optional): If the call is using the wrapper. Defaults to False.
            with_env_var (bool, optional): If the call is using an environment variable defined in .gitlab-ci.yml. Defaults to False.
        """
        self.file = file
        self.line_nb = line_nb
        self.with_wrapper = with_wrapper
        self.with_env_var = with_env_var

    def __str__(self):
        message = ""
        if not self.with_wrapper:
            message += "Please use the dedicated `fetch_secret.(sh|ps1)`."
        if not self.with_env_var:
            message += " Save your parameter name as environment variable in .gitlab-ci.yml file."
        return f"{self.file}:{self.line_nb + 1}. {message}"

    def __repr__(self):
        return str(self)


def list_get_parameter_calls(file):
    aws_ssm_call = re.compile(r"^.+ssm get-parameter.+--name +(?P<param>[^ ]+).*$")
    # remove the first letter of the script name because '\f' is badly interpreted for windows paths
    wrapper_call = re.compile(r"^.+etch_secret.(sh|ps1)[\"]? (-parameterName )?+(?P<param>[^ )]+).*$")
    calls = []
    with open(file) as f:
        try:
            for nb, line in enumerate(f):
                m = aws_ssm_call.match(line.strip())
                if m:
                    # Remove possible quotes
                    param = m["param"].replace('"', '').replace("'", "")
                    calls.append(
                        SSMParameterCall(file, nb, with_env_var=(param.startswith("$") or "os.environ" in param))
                    )
                m = wrapper_call.match(line.strip())
                param = m["param"].replace('"', '').replace("'", "") if m else None
                if m and not (param.startswith("$") or "os.environ" in param):
                    calls.append(SSMParameterCall(file, nb, with_wrapper=True))
        except UnicodeDecodeError:
            pass
    return calls


@task
def gitlab_ci(ctx, test="all", custom_context=None):
    """
    Lint Gitlab CI files in the datadog-agent repository.

    This will lint the main gitlab ci file with different
    variable contexts and lint other triggered gitlab ci configs.
    """

    agent = get_gitlab_repo()
    has_errors = False

    print(f'{color_message("info", Color.BLUE)}: Fetching Gitlab CI configurations...')
    configs = get_all_gitlab_ci_configurations(ctx)

    def test_gitlab_configuration(entry_point, input_config, context=None):
        nonlocal has_errors

        # Update config and lint it
        config = generate_gitlab_full_configuration(ctx, entry_point, context=context, input_config=input_config)
        res = agent.ci_lint.create({"content": config, "dry_run": True, "include_jobs": True})
        status = color_message("valid", "green") if res.valid else color_message("invalid", "red")

        print(f"{color_message(entry_point, Color.BOLD)} config is {status}")
        if len(res.warnings) > 0:
            print(
                f'{color_message("warning", Color.ORANGE)}: {color_message(entry_point, Color.BOLD)}: {res.warnings})',
                file=sys.stderr,
            )
        if not res.valid:
            print(
                f'{color_message("error", Color.RED)}: {color_message(entry_point, Color.BOLD)}: {res.errors})',
                file=sys.stderr,
            )
            has_errors = True

    for entry_point, input_config in configs.items():
        with gitlab_section(f"Testing {entry_point}", echo=True):
            # Only the main config should be tested with all contexts
            if entry_point == ".gitlab-ci.yml":
                all_contexts = []
                if custom_context:
                    all_contexts = load_context(custom_context)
                else:
                    all_contexts = get_preset_contexts(test)

                print(f'{color_message("info", Color.BLUE)}: We will test {len(all_contexts)} contexts')
                for context in all_contexts:
                    print("Test gitlab configuration with context: ", context)
                    test_gitlab_configuration(entry_point, input_config, dict(context))
            else:
                test_gitlab_configuration(entry_point, input_config)

    if has_errors:
        raise Exit(code=1)


@task
def releasenote(ctx):
    """
    Lint release notes with Reno
    """
    branch = os.environ.get("BRANCH_NAME")
    pr_id = os.environ.get("PR_ID")

    run_check = is_pr_context(branch, pr_id, "release note")
    if run_check:
        github = GithubAPI(repository=GITHUB_REPO_NAME, public_repo=True)
        if github.is_release_note_needed(pr_id):
            if not github.contains_release_note(pr_id):
                print(
                    f"{color_message('Error', 'red')}: No releasenote was found for this PR. Please add one using 'reno'"
                    ", see https://datadoghq.dev/datadog-agent/guidelines/contributing/#reno"
                    ", or apply the label 'changelog/no-changelog' to the PR.",
                    file=sys.stderr,
                )
                raise Exit(code=1)
            ctx.run("reno lint")
        else:
            print("'changelog/no-changelog' label found on the PR: skipping linting")


@task
def update_go(_):
    _update_references(warn=False, version="1.2.3", dry_run=True)
    _update_go_mods(warn=False, version="1.2.3", include_otel_modules=True, dry_run=True)


@task(iterable=['job_files'])
def job_change_path(ctx, job_files=None):
    """
    Verify that the jobs defined within job_files contain a change path rule.
    """

    tests_without_change_path_allow_list = {
        'generate-flakes-finder-pipeline',
        'k8s-e2e-cspm-dev',
        'k8s-e2e-cspm-main',
        'k8s-e2e-otlp-dev',
        'k8s-e2e-otlp-main',
        'new-e2e-agent-platform-install-script-amazonlinux-a6-arm64',
        'new-e2e-agent-platform-install-script-amazonlinux-a6-x86_64',
        'new-e2e-agent-platform-install-script-amazonlinux-a7-arm64',
        'new-e2e-agent-platform-install-script-amazonlinux-a7-x64',
        'new-e2e-agent-platform-install-script-centos-a6-x86_64',
        'new-e2e-agent-platform-install-script-centos-a7-x86_64',
        'new-e2e-agent-platform-install-script-centos-dogstatsd-a7-x86_64',
        'new-e2e-agent-platform-install-script-centos-fips-a6-x86_64',
        'new-e2e-agent-platform-install-script-centos-fips-a7-x86_64',
        'new-e2e-agent-platform-install-script-centos-fips-dogstatsd-a7-x86_64',
        'new-e2e-agent-platform-install-script-centos-fips-iot-agent-a7-x86_64',
        'new-e2e-agent-platform-install-script-centos-iot-agent-a7-x86_64',
        'new-e2e-agent-platform-install-script-debian-a6-arm64',
        'new-e2e-agent-platform-install-script-debian-a6-x86_64',
        'new-e2e-agent-platform-install-script-debian-a7-arm64',
        'new-e2e-agent-platform-install-script-debian-a7-x86_64',
        'new-e2e-agent-platform-install-script-debian-dogstatsd-a7-x86_64',
        'new-e2e-agent-platform-install-script-debian-heroku-agent-a6-x86_64',
        'new-e2e-agent-platform-install-script-debian-heroku-agent-a7-x86_64',
        'new-e2e-agent-platform-install-script-debian-iot-agent-a7-x86_64',
        'new-e2e-agent-platform-install-script-suse-a6-x86_64',
        'new-e2e-agent-platform-install-script-suse-a7-arm64',
        'new-e2e-agent-platform-install-script-suse-a7-x86_64',
        'new-e2e-agent-platform-install-script-suse-dogstatsd-a7-x86_64',
        'new-e2e-agent-platform-install-script-suse-iot-agent-a7-x86_64',
        'new-e2e-agent-platform-install-script-ubuntu-a6-arm64',
        'new-e2e-agent-platform-install-script-ubuntu-a6-x86_64',
        'new-e2e-agent-platform-install-script-ubuntu-a7-arm64',
        'new-e2e-agent-platform-install-script-ubuntu-a7-x86_64',
        'new-e2e-agent-platform-install-script-ubuntu-dogstatsd-a7-x86_64',
        'new-e2e-agent-platform-install-script-ubuntu-heroku-agent-a6-x86_64',
        'new-e2e-agent-platform-install-script-ubuntu-heroku-agent-a7-x86_64',
        'new-e2e-agent-platform-install-script-ubuntu-iot-agent-a7-x86_64',
        'new-e2e-agent-platform-install-script-docker',
        'new-e2e-agent-platform-install-script-upgrade6-amazonlinux-x64',
        'new-e2e-agent-platform-install-script-upgrade6-centos-fips-x86_64',
        'new-e2e-agent-platform-install-script-upgrade6-centos-x86_64',
        'new-e2e-agent-platform-install-script-upgrade6-debian-x86_64',
        'new-e2e-agent-platform-install-script-upgrade6-suse-x86_64',
        'new-e2e-agent-platform-install-script-upgrade6-ubuntu-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-amazonlinux-iot-agent-x64',
        'new-e2e-agent-platform-install-script-upgrade7-amazonlinux-x64',
        'new-e2e-agent-platform-install-script-upgrade7-centos-fips-iot-agent-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-centos-fips-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-centos-iot-agent-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-centos-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-debian-iot-agent-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-debian-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-suse-iot-agent-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-suse-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-ubuntu-iot-agent-x86_64',
        'new-e2e-agent-platform-install-script-upgrade7-ubuntu-x86_64',
        'new-e2e-agent-platform-rpm-centos6-a7-x86_64',
        'new-e2e-agent-platform-step-by-step-amazonlinux-a6-arm64',
        'new-e2e-agent-platform-step-by-step-amazonlinux-a6-x86_64',
        'new-e2e-agent-platform-step-by-step-amazonlinux-a7-arm64',
        'new-e2e-agent-platform-step-by-step-amazonlinux-a7-x64',
        'new-e2e-agent-platform-step-by-step-centos-a6-x86_64',
        'new-e2e-agent-platform-step-by-step-centos-a7-x86_64',
        'new-e2e-agent-platform-step-by-step-debian-a6-arm64',
        'new-e2e-agent-platform-step-by-step-debian-a6-x86_64',
        'new-e2e-agent-platform-step-by-step-debian-a7-arm64',
        'new-e2e-agent-platform-step-by-step-debian-a7-x64',
        'new-e2e-agent-platform-step-by-step-suse-a6-x86_64',
        'new-e2e-agent-platform-step-by-step-suse-a7-arm64',
        'new-e2e-agent-platform-step-by-step-suse-a7-x86_64',
        'new-e2e-agent-platform-step-by-step-ubuntu-a6-arm64',
        'new-e2e-agent-platform-step-by-step-ubuntu-a6-x86_64',
        'new-e2e-agent-platform-step-by-step-ubuntu-a7-arm64',
        'new-e2e-agent-platform-step-by-step-ubuntu-a7-x86_64',
        'new-e2e-agent-shared-components',
        'new-e2e-cws',
        'new-e2e-language-detection',
        'new-e2e-npm-docker',
        'new-e2e-npm-packages',
        'new-e2e-orchestrator',
        'new-e2e-package-signing-amazonlinux-a6-x86_64',
        'new-e2e-package-signing-debian-a7-x86_64',
        'new-e2e-package-signing-suse-a7-x86_64',
        'new-e2e_windows_powershell_module_test',
        'trigger-flakes-finder',
    }

    job_files = job_files or (['.gitlab/e2e/e2e.yml'] + list(glob('.gitlab/e2e/install_packages/*.yml')))

    # Read and parse gitlab config
    # The config is filtered to only include jobs
    config = get_gitlab_ci_configuration(ctx, ".gitlab-ci.yml")

    # Fetch all test jobs
    test_config = read_includes(ctx, job_files, return_config=True, add_file_path=True)
    tests = [(test, data['_file_path']) for test, data in test_config.items() if test[0] != '.']

    def contains_valid_change_rule(rule):
        """
        Verifies that the job rule contains the required change path configuration.
        """
        if 'changes' not in rule or 'paths' not in rule['changes']:
            return False

        # The change paths should be more than just test files
        return any(
            not path.startswith(('test/', './test/', 'test\\', '.\\test\\')) for path in rule['changes']['paths']
        )

    # Verify that all tests contain a change path rule
    tests_without_change_path = defaultdict(list)
    tests_without_change_path_allowed = defaultdict(list)
    for test, filepath in tests:
        if not any(contains_valid_change_rule(rule) for rule in config[test]['rules'] if isinstance(rule, dict)):
            if test in tests_without_change_path_allow_list:
                tests_without_change_path_allowed[filepath].append(test)
            else:
                tests_without_change_path[filepath].append(test)

    if len(tests_without_change_path_allowed) != 0:
        with gitlab_section('Allow-listed jobs', collapsed=True):
            print(
                color_message(
                    'warning: The following tests do not contain required change paths rule but are allowed:',
                    Color.ORANGE,
                )
            )
            for filepath, tests in tests_without_change_path_allowed.items():
                print(f"- {color_message(filepath, Color.BLUE)}: {', '.join(tests)}")
            print(color_message('warning: End of allow-listed jobs', Color.ORANGE))
            print()

    if len(tests_without_change_path) != 0:
        print(color_message("error: Tests without required change paths rule:", "red"), file=sys.stderr)
        for filepath, tests in tests_without_change_path.items():
            print(f"- {color_message(filepath, Color.BLUE)}: {', '.join(tests)}", file=sys.stderr)

        raise RuntimeError(
            color_message(
                'Some tests do not contain required change paths rule, they must contain at least one non-test path.',
                Color.RED,
            )
        )
    else:
        print(color_message("success: All tests contain a change paths rule or are allow-listed", "green"))


@task
def gitlab_change_paths(ctx):
    # Read gitlab config
    config = generate_gitlab_full_configuration(ctx, ".gitlab-ci.yml", {}, return_dump=False, apply_postprocessing=True)
    error_paths = []
    for path in set(retrieve_all_paths(config)):
        files = glob(path, recursive=True)
        if len(files) == 0:
            error_paths.append(path)
    if error_paths:
        raise Exit(
            f"{color_message('No files found for paths', Color.RED)}:\n{chr(10).join(' - ' + path for path in error_paths)}"
        )
    print(f"All rule:changes:paths from gitlab-ci are {color_message('valid', Color.GREEN)}.")
