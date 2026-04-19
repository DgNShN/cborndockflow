# Contributing to cborn DocFlow

Thanks for your interest in improving cborn DocFlow.

## Before you start

- Fork the repository.
- Create a feature branch from `main`.
- Make sure your changes fit the existing style and structure.
- Keep the app local-first unless a change clearly needs network access.

## Development workflow

1. Install dependencies from `requirements.txt`.
2. Run the app with `python main.py`.
3. Test the area you changed.
4. Keep commits focused and easy to review.

## Code and docs

- Prefer small, clear changes.
- Update `README.md` when behavior or setup changes.
- Avoid committing secrets, credentials, or local machine files.

## Pull requests

- Describe what changed and why.
- Mention any manual testing you performed.
- Include screenshots for UI changes when useful.

## Release quality

- Keep changes safe for Windows users.
- Preserve existing OCR and tagging behavior unless a change is intentional.
- If you add new config options, provide sensible defaults.
