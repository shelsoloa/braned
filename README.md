# braned

## Installation mac

- install python with sqlite extensions enabled

> Following works on mac M1

```bash
brew install sqlite3 openssl
pyenv uninstall 3.12.8
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions --with-openssl=$(brew --prefix openssl)" \
    LDFLAGS="-L/opt/homebrew/opt/sqlite/lib" \
    CPPFLAGS="-I/opt/homebrew/opt/sqlite/include" \
    pyenv install 3.12.8
```
