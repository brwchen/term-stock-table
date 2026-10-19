Output assets/features/intraday_and_chips.gif
Set Shell "bash"
Set FontSize 16
Set Width 1600
Set Height 1000
Set Padding 12
Set Theme "Catppuccin Mocha"
Type "stk --intraday 600519 --sim"
Enter
Sleep 3s
Type "clear && stk --chips 600519 --sim"
Enter
Sleep 3s
