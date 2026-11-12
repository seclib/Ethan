PREFIX ?= $(HOME)/.local
BINDIR = $(PREFIX)/bin
CONFDIR = $(PREFIX)/etc/ethan-shell
XDGDIR = $(PREFIX)/share/applications

.PHONY: install uninstall clean

install:
	@echo "== Installing ETHAN Shell Integration Layer =="
	install -d $(BINDIR) $(CONFDIR)/adapters $(CONFDIR)/cli $(CONFDIR)/launcher $(CONFDIR)/xdg
	install -m 755 cli/send.sh $(BINDIR)/ethan-send
	install -m 755 cli/status.sh $(BINDIR)/ethan-status
	install -m 755 launcher/ethan-launcher.sh $(BINDIR)/ethan-launcher
	install -m 755 xdg/ethan-shortcut.sh $(BINDIR)/ethan-shortcut
	install -m 644 adapters/bash/ethan.bash $(CONFDIR)/adapters/bash.bash
	install -m 644 adapters/zsh/ethan.zsh $(CONFDIR)/adapters/zsh.zsh
	install -m 644 adapters/fish/ethan.fish $(CONFDIR)/adapters/fish.fish
	@echo "Installed to $(PREFIX)"
	@echo "Add to your shell rc:"
	@echo "  bash: source $(CONFDIR)/adapters/bash.bash"
	@echo "  zsh:  source $(CONFDIR)/adapters/zsh.zsh"
	@echo "  fish: source $(CONFDIR)/adapters/fish.fish"

uninstall:
	rm -f $(BINDIR)/ethan-send $(BINDIR)/ethan-status $(BINDIR)/ethan-launcher $(BINDIR)/ethan-shortcut
	rm -rf $(CONFDIR)
	@echo "Uninstalled."

clean:
	rm -f completion/completions/*