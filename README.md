# Zero-Cost Bitcoin Workbench

A small Python project for drafting digital-work ideas from local templates and keeping a checklist for reward opportunities whose current rules explicitly permit automation.

It does not contact platforms, sign in to accounts, click, submit tasks, mine Bitcoin, create Bitcoin, or promise income. It uses no AI model or paid API. Drafts are starting points to edit and check yourself.

## What it does

- Creates practical service ideas and content drafts using templates stored in `data/draft_templates.json`.
- Tracks reward opportunities only when you provide a terms URL and confirm that the current rules explicitly permit the automation you intend to use.
- Keeps the reward checklist and evidence notes in a local JSON file.
- Runs locally or in GitHub Actions. The workflow generates a draft and uploads it together with a tracker snapshot as an artifact.

The app never performs any reward-task steps. You must use the official platform yourself, follow its current rules, and verify any reward with a real receipt before recording it.

## Requirements

- Python 3.11 or newer.
- No Python packages or paid AI/API account.

The workflow uses standard GitHub-hosted Ubuntu runners and current major versions of GitHub-maintained Actions. GitHub Actions usage is free for standard runners in public repositories. Private repositories have plan-based included minutes and storage, and usage beyond the allowance can be billed. See [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## Run locally

Open a terminal in the repository folder:

```bash
python -m workbench ideas --skill "writing and proofreading" --audience "small local businesses"
python -m workbench draft --topic "a clear one-page service menu" --format service_listing --audience "small local businesses"
```

Generated files are saved under `output/`.

### Track an allowed reward opportunity

Only add an opportunity after reading its current terms. The app requires an official terms URL, your note quoting or summarizing the policy section, and an explicit confirmation flag:

```bash
python -m workbench task add \
  --title "Example task name" \
  --platform "Example platform" \
  --terms-url "https://example.com/terms" \
  --policy-evidence "Terms section 4.2 says the specific automation used for this task is allowed." \
  --automation-permitted
```

The sample URL above is only a placeholder. Replace it with the platform's real rules page and evidence that applies to the exact activity. If permission is unclear, do not add or automate the opportunity.

List tasks and checklist items:

```bash
python -m workbench task list
python -m workbench task show TASK_ID
```

Mark a checklist item after you personally complete it:

```bash
python -m workbench task check TASK_ID eligibility_checked --done
python -m workbench task check TASK_ID policy_rechecked --done
python -m workbench task check TASK_ID manual_submission --done
python -m workbench task check TASK_ID truthful_submission --done
```

`TASK_ID` is printed when the task is added. For a reward task, the checklist expects you to review eligibility and policy again, do the work through the official interface, and submit truthful work. The app has no command for logging projected or expected earnings. It only includes user-entered, confirmed receipts in its tracker snapshot.

### Generate a tracker snapshot

```bash
python -m workbench snapshot
```

This writes `output/reward_tracker.json` and `output/reward_report.md`.

## Exact GitHub repository setup

1. Sign in to GitHub and create a new, empty repository. Do not initialize it with a README or license. Use a private repository if your task titles or notes are personal. Do not put passwords, API tokens, wallet seed phrases, or private keys in the repository.
2. Download and extract this ZIP. Open a terminal in the extracted `zero-cost-bitcoin-workbench` folder, then run the following commands after replacing the repository URL with yours:

   ```bash
   git init -b main
   git add .
   git commit -m "Add Zero-Cost Workbench"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
   git push -u origin main
   ```

   Git will ask you to authenticate with GitHub if needed. These commands publish the workflow and code; they do not configure any secrets or credentials for the app.
3. Confirm the push completed and the workflow file appears at `.github/workflows/daily-workbench.yml` on the default branch. GitHub only enables scheduled and manual triggers after the workflow file is present there.
4. Open the repository's **Actions** tab. If prompted, enable workflows. Select **Zero-Cost Workbench**, choose **Run workflow**, enter a topic if desired, and run it.
5. Open the completed run and download the `workbench-output` artifact. It contains the generated draft, a snapshot of `data/reward_tasks.json`, and a readable checklist report.
6. To retain tracker changes between cloud runs, edit `data/reward_tasks.json` locally and commit/push that file to the default branch. Each Actions run starts from the repository contents; GitHub Actions does not commit changes back.

The scheduled run is daily at **17:37 UTC**. GitHub may delay or skip scheduled runs during high load; a schedule is a convenience, not a guaranteed alarm. You can change the cron expression in `.github/workflows/daily-workbench.yml`.

To disable the schedule, remove the `schedule` section or disable the workflow from the repository's Actions page. Manual runs can still be used if `workflow_dispatch` remains enabled.

## Files

```text
.github/workflows/daily-workbench.yml   Scheduled and manual GitHub Actions workflow
data/draft_templates.json               Editable local writing templates
data/reward_tasks.json                  Local reward-task checklist data
workbench/                              Python CLI and application logic
tests/                                  Standard-library unit tests
```

## Safety and accuracy

- No account credentials, wallet private keys, or seed phrases are needed or read.
- No network requests are made by the Python app.
- A policy URL and evidence note are recorded for each reward opportunity. The app does not fetch or validate that policy; you must reread it because rules can change.
- A “permitted” confirmation is your own record, not a legal determination or guarantee the platform will accept the work.
- The app never executes, clicks, solves, submits, or claims a reward. It is a planner and record keeper only.
- The app records reward receipts only when you explicitly mark a reward as received and enter a positive amount, currency, and evidence note. The note and amount are user-reported and are not independently verified.
- Drafts are template-generated, not researched or fact-checked. Edit them, respect copyright and platform rules, and make no unsupported claims.
- This project does not mine Bitcoin, create Bitcoin, or guarantee earnings. Revenue may be zero.

## Check the project

```bash
python -m unittest discover -s tests -v
python -m workbench --help
```
