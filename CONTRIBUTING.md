# Contributing to computer-lockdown

Thanks for your interest in improving computer-lockdown! This guide
covers how to get set up and how to submit changes.

## Development setup

1. Fork and clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Making changes

1. Create a feature branch off `main`:
   ```bash
   git checkout -b my-feature
   ```
2. Make your change, keeping commits focused and messages descriptive.
3. Test locally before opening a pull request.

## Submitting a pull request

1. Push your branch and open a pull request against `main`.
2. Describe **what** changed and **why**.
3. Link any related issues.

## Reporting issues

Open an issue with clear reproduction steps, your OS version, and what
you expected to happen versus what actually happened.
