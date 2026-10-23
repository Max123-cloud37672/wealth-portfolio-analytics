# Development log

A record of what was built, the decisions made, the problems I hit and what I
learned.

## Friday 23 October 2026

### What was built

| Milestone | Pull request |
|---|---|
| Project setup: virtual environment, pinned dependencies, pytest, Ruff and CI | #1 |
| `Transaction`, `Position` and `Portfolio`: replaying trades into holdings | #2 |
| MySQL storage: schema, repositories, a separate test database, sample clients and trades, CI with a MySQL service | #3 |
| Securities, simulated daily prices, `PriceHistory` and `Performance` (time-weighted return) | #4 |
| Interactive Streamlit dashboard with validated trade entry | #5 |
| README, DEVLOG and screenshots | #6 |

### Decisions

- **A second project rather than extending the first.** My first project
  tracked a snapshot of holdings from CSV files. The brief for this one was
  Python with a local MySQL database, so I started a new repository built
  around a trade history.
- **Store facts, calculate everything else.** MySQL holds clients, trades,
  securities and prices. Positions, average costs and returns are always
  calculated from the trades, so the numbers can never drift out of step with
  the history they come from.
- **Repository classes for all SQL,** with values passed as parameters. This
  keeps SQL in one place and prevents SQL injection.
- **A separate test database,** emptied before each test. A safety check stops
  the tests if it ever has the same name as the real database.
- **The password stays out of the code.** MySQL login details live in `.env`,
  which Git ignores. CI uses a throwaway password that only exists on GitHub's
  temporary machine.
- **Time-weighted return,** because it is the standard way to report
  performance when clients add and withdraw money. A simple gain percentage is
  distorted by the timing of deposits.
- **Simulated prices that match the trades.** Rather than drawing random
  prices, each price series is pinned to the sample trade prices, so every trade
  happened at that day's closing price.
- **Clients of different sizes,** from about $300K to about $5M, with
  Conservative, Balanced and Growth risk profiles.
- **The trade form runs the same checks as the code.** A new trade is replayed
  with the client's whole history before it is saved, which also catches a
  back-dated sale that would break a later one.

### Problems and how they were fixed

| Problem | Cause | Fix |
|---|---|---|
| Two copies of the project on my Mac | The repository ended up in both my home folder and Documents | Picked one (`~/wealth-portfolio-analytics`) and worked only there |
| `zsh: no such file or directory: cd~/wealth-portfolio-analytics` | Missing space after `cd` | `cd ~/wealth-portfolio-analytics` |
| An empty `transaction.py` appeared in `src/` | Created the file in the wrong folder | Deleted it; the real file belongs in `src/wealth_analytics/` |
| A commit message came out as `feat: store clients and transactions a MYSQL service`, and the second commit was missing | Two commit commands got mixed together | `git commit --amend` to fix the message, made the missing commit, then `git push --force-with-lease` (only ever on my own branch) |
| Ruff said the imports were in the wrong order | Ruff didn't know `wealth_analytics` was this project's own package, because the file didn't exist yet | Added `known-first-party` to `pyproject.toml` |
| A dashboard test changed the wrong dropdown | The test picked the dropdown by its position on the page | Gave every input a `key` and selected it by name |
| The "Net invested" line sloped between days | Plotly joins points with straight lines by default | Drew it as steps, because money arrives on a single day |
| The Weight column was cut off the holdings table | The table was wider than the page | Removed the Asset type column (the chart already shows it) and moved Weight next to Value |
| The PR said "Checking for ability to merge automatically" for a while | GitHub was still starting CI, which now has to boot MySQL first | Waited for the green check |

### What I learned

- **Databases:** A table is like a spreadsheet with strict rules. A primary key
  identifies each row, and a foreign key links rows between tables, for example
  each trade to its client. Constraints let MySQL itself reject bad data.
  Passing values as parameters instead of building SQL strings is what stops
  SQL injection.
- **Performance:** Market value minus net invested gives the total gain.
  Time-weighted return strips out the effect of deposits and withdrawals,
  which is why it can differ from the simple gain percentage. It is also the
  fair way to compare a portfolio with a benchmark.
- **Testing:** Tests can run against a real database if each test starts from
  a clean, separate one. Checking a result two independent ways, as with total
  gain against realized plus unrealized gain, catches mistakes that a single
  test would miss.
- **Git and GitHub:** Splitting work into commits by type (`feat`, `ci`,
  `chore`) makes the history easier to read. `--amend` fixes the last commit.
  `--force-with-lease` is only for my own branches, never `main`. I don't need
  to pull before opening a pull request, only after merging.
- **CI:** GitHub Actions can start its own MySQL server for the tests, so CI
  checks the database code too, not just the Python.
- **Working with an AI assistant:** In this project Claude wrote all of the
  code. My part was choosing the requirements, approving each step, running
  everything locally and managing Git. To be ready to explain it, I am going
  through how each part works, starting from the README's calculations
  section. Next time I want to write more of the code myself.
