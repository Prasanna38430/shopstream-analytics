# Contributing

This is a personal portfolio project, so I'm not really expecting pull requests. That said, if you cloned it and something didn't work, or you spotted a bug or a cleaner way to do something, I'd genuinely like to hear about it. Open an issue with what you ran and what happened.

If you do want to change something and send a PR, a few notes that will save you time:

- The dbt project lives in `dbt/shopstream`. Run `dbt build` from there after loading the raw data, or it won't have anything to build on.
- Great Expectations has to go in its own virtualenv (`requirements-quality.txt`). It shares dependencies with dbt that don't resolve together, so don't try to install both in one environment.
- CI runs `pytest` and `dbt build --target ci` on every push. The CI target writes to separate schemas, so it won't touch real data, but it does need Snowflake credentials set as repository secrets.
- Keep credentials out of commits. There's a `.env.example` showing the shape of what's needed; the real `.env` is gitignored and should stay that way.

Commit messages here are written like normal sentences rather than a strict convention, so just describe what you did.
