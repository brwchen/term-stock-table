Output assets/features/watchlist_management.gif
Set Shell "bash"
Set FontSize 16
Set Width 1600
Set Height 600
Set Padding 12
Set Theme "Catppuccin Mocha"
Hide
Type "export HOME=$(mktemp -d) && clear"
Enter
Show
Type "stk --add TSLA"
Enter
Sleep 1s
Type "stk --list"
Enter
Sleep 2s
Type "stk --remove TSLA && stk --list"
Enter
Sleep 3s
