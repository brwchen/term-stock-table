Output assets/features/portfolio_pnl_tracker.gif
Set Shell "bash"
Set FontSize 16
Set Width 1900
Set Height 700
Set Padding 12
Set Theme "Catppuccin Mocha"
Hide
Type "export HOME=$(mktemp -d) && clear"
Enter
Type "stk --position 600519 100 1300 && stk --position AAPL 50 300 && clear"
Enter
Show
Type "stk --portfolio --sim"
Enter
Sleep 4s
