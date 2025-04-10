
[![Lint](https://github.com/zackees/static-graphviz/actions/workflows/lint.yml/badge.svg)](https://github.com/zackees/static-graphviz/actions/workflows/lint.yml)
[![MacOS_Tests](https://github.com/zackees/static-graphviz/actions/workflows/push_macos.yml/badge.svg)](https://github.com/zackees/static-graphviz/actions/workflows/push_macos.yml)
[![Win_Tests](https://github.com/zackees/static-graphviz/actions/workflows/push_win.yml/badge.svg)](https://github.com/zackees/static-graphviz/actions/workflows/push_win.yml)
[![Ubuntu_Tests](https://github.com/zackees/static-graphviz/actions/workflows/push_ubuntu.yml/badge.svg)](https://github.com/zackees/static-graphviz/actions/workflows/push_ubuntu.yml)

## Update Instructions

#### Ubuntu

Install graphviz as usual with `apt-get install -y graphviz`

```
mkdir -p temp_package/bin
mkdir -p temp_package/lib

# Copy the 'dot' binary
cp -v $(which dot) temp_package/bin/

# Copy all .so dependencies
ldd $(which dot) | awk '{print $3}' | grep '^/' | xargs -I{} cp -v {} temp_package/lib/

# Create the compressed tarball
tar -cJf graphviz-portable.tar.xz -C temp_package .
```
