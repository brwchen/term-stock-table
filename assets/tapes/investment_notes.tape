Output assets/features/investment_notes.gif
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
Type "stk --note 600519 'Core holding, add below 1300'"
Enter
Sleep 1s
Type "stk --notes 600519"
Enter
Sleep 3s
