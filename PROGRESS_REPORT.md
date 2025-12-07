Avalytics - Project Progress Report (Weeks 2 & 3)

Project: Avalytics - AI-Augmented Blockchain CRM Platform
Student: Naman Bajpai (nb3283)
Repository: https://github.com/bajpainaman/Avalytics
Report Date: Week 3 (submitting weeks 2 & 3 together)

Note: I missed submitting the week 2 progress report, so I'm including both weeks 2 and 3 here.


Contract Checklist

Planned Features Status:

Indexer Node - DONE
  - Backend AvalancheGo node setup complete
  - Added test connection script
  - Status: Working, tested connection to local node

Query CLI - MOSTLY DONE
  - Basic query commands implemented
  - Can query blocks, transactions, and block ranges
  - Address filtering works
  - Chain performance stats command added
  - Status: Working, might add more features later

Analytics Dashboard - MOSTLY DONE
  - Dashboard command added to CLI
  - Interactive mode works
  - Chain performance stats integrated
  - Status: Working, could use more visualizations

ML Cohort Clustering - NOT STARTED
  - Code exists but haven't tested it yet

Off-Chain Research Agents - NOT STARTED
  - Code exists but haven't integrated it

CRM Sync & Lead Generation - NOT STARTED
  - Code exists but haven't tested it

End-to-End Pipeline Orchestration - NOT STARTED
  - Haven't started connecting everything together


Work Completed - Week 2 (Nov 3-8)

Naman Bajpai

This week I worked on testing the backend setup and starting the Query CLI.

First I added a test script to check if the AvalancheGo node is actually running and responding. It checks the health endpoint and tries a basic RPC call to make sure everything works.

Then I started implementing the Query CLI. Added a basic query command that can query a specific block by number or a transaction by hash. It connects to either the local node or public API depending on what's available.

I improved the query command to have better display formatting with tables, and added address filtering so you can see transactions for a specific address within blocks.

Added transaction query functionality so you can look up transactions by hash and see details like value, gas used, status, etc.

Updated the indexer config to automatically use local node if it's running, otherwise falls back to public API. This makes it easier to switch between local and remote.

Finally updated the backend README to include the test connection script.

Commits made:
- dc70d77 - Test script for backend connection
- d524a23 - Basic query command
- 2cb60a6 - Improved query display
- e9ad864 - Indexer uses local node
- ed34c72 - Transaction query support
- 97abfd5 - Updated README

I tested the backend node connection and it works. The query CLI is functional but still pretty basic at this point.


Work Completed - Week 3 (Nov 10-15)

Naman Bajpai

This week I focused on completing the Query CLI and integrating the dashboard.

I implemented the block range queries that were showing "coming soon" before. Now you can use --from-block and --to-block to query a range of blocks. It can handle up to 100 blocks at a time and shows stats like total transactions, gas used, etc. Added a progress bar so you know it's working.

Enhanced the block range queries to filter transactions by address. Now you can see all transactions for a specific address across a range of blocks, which is useful for tracking wallet activity.

Added a new chain-stats command that calculates TPS (transactions per second), average gas per block, average block time, and volume. It analyzes the last N blocks (default 100) and gives you performance metrics.

Added a dashboard command to the CLI so you can launch the interactive dashboard. It connects to the database and shows analytics in a terminal interface.

Added chain performance stats view to the dashboard. You can see real-time chain metrics in the interactive mode, which is helpful for monitoring.

Fixed some error handling issues in the chain stats calculation. There were some division by zero edge cases that could crash it.

Updated the README with examples of the new query and dashboard commands so people know how to use them.

Commits made:
- 1faab9c - Block range query implementation
- 619cb9a - Address filtering for block ranges
- 74e4f89 - Chain performance stats command
- ae288a2 - Dashboard command integration
- 93bf930 - Chain stats in dashboard
- cf5ba81 - Error handling fixes
- 05663c4 - README updates

The Query CLI is basically done now. The dashboard works but could use more features. Next I need to work on connecting everything together and testing the ML clustering stuff.


Work Planned for Next Week

Naman Bajpai

Next week I plan to:

1. Test ML cohort clustering - The code exists but I haven't actually run it yet. Need to test it and make sure it works.

2. Start pipeline integration - Connect the indexer to actually write to the database, then have the dashboard read from it. Right now things are kind of separate.

3. Test off-chain research agents - The Perplexity and Grok clients exist but I haven't tested them. Need to make sure they work and integrate them.

4. Maybe start CRM sync - If I have time, start testing the Monday.com integration.

That's probably enough for ~5 hours of work. I'll focus on getting the existing pieces to actually work together.

Estimated Time: 5 hours/week


Git Contributors

Git Usernames and Associated Group Members:

1. Naman Bajpai (95096343+bajpainaman@users.noreply.github.com)
   - Primary contributor
   - All commits authored by this account

2. Naman Bajpai (E189395@exelonds.com)
   - Alternative email, same person

3. Naman Bajpai (bajpainaman@gmail.com)
   - Alternative email, same person

4. copilot-swe-agent[bot] (198982749+Copilot@users.noreply.github.com)
   - GitHub Copilot automated suggestions
   - Not a group member

Note: This is a solo project. All development work is done by Naman Bajpai.


Notes

- Solo project, just me working on it
- Meeting schedule: Before classes when I have time
- Time commitment: ~5 hours per week
- Sorry about missing week 2 report, submitting both together now
- Making good progress on Query CLI and dashboard
- Need to focus on integration next


Commit History

Week 2 commits (Nov 3-8):
- 6 commits related to Query CLI and backend testing

Week 3 commits (Nov 10-15):
- 7 commits completing Query CLI and dashboard integration

Total: 13 commits across both weeks


Progress report for Avalytics project - Weeks 2 & 3
