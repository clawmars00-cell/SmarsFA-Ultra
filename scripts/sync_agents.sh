#!/bin/bash
# Sync agents from GitHub to OpenClaw

REPO_URL="https://github.com/clawmars00-cell/SmarsFA-Ultra.git"
LOCAL_REPO="/tmp/SmarsFA-Ultra"
OPENCLAW_AGENTS="/home/mars/.openclaw/agents/smarsfa_ultra"

echo "=== Syncing SmarsFA-Ultra Agents ==="

# Clone or pull
if [ -d "$LOCAL_REPO/.git" ]; then
    cd $LOCAL_REPO && git pull origin master
else
    git clone $REPO_URL $LOCAL_REPO
fi

# Sync each agent
for agent in master parsing trend sentiment whale risk synthesis; do
    SRC="$LOCAL_REPO/docs/agents/$agent"
    DEST="$OPENCLAW_AGENTS/$agent/agent"
    
    if [ -d "$SRC" ]; then
        cp -f $SRC/*.md $DEST/
        echo "✓ Synced $agent"
    fi
done

echo "=== Done ==="
