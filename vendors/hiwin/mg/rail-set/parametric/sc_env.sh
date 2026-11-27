set -e; B=$HOME/.local/opt/solidcraft-0.50.0-linux-x86_64/bin; if [ ! -x $B/solidcraft-cli ]; then T=$(mktemp -d); curl -fsSL https://github.com/tangency-labs/solidcraft/releases/download/v0.50.0/solidcraft-0.50.0-linux-x86_64.tar.gz | tar -xz -C $T; B=$(dirname $(find $T -name solidcraft-cli -type f | head -1)); fi
export SC_CLI=$B/solidcraft-cli SC_APP=$B/solidcraft; "$@"
