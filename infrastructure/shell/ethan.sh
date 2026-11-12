# ETHAN Shell Integration — Source dans .bashrc
# Usage: echo "source /etc/ethan/shell/ethan.sh" >> ~/.bashrc

ETHAN_HOME="${ETHAN_HOME:-$HOME/.ethan}"
export PATH="$ETHAN_HOME/bin:$PATH"

# Autocomplete
if [ -f /etc/ethan/shell/completion.sh ]; then
    source /etc/ethan/shell/completion.sh
fi

# Alias
alias ethan-status='systemctl --user status ethan-core'
alias ethan-logs='journalctl --user -u ethan-core -f'
alias ethan-start='systemctl --user start ethan-core'
alias ethan-stop='systemctl --user stop ethan-core'
alias ethan-restart='systemctl --user restart ethan-core'