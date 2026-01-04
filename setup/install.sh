#!/bin/bash
set -e

CONFIG_FILE="config.yaml"
# Defaults
DEFAULT_REGION="switzerland"
DEFAULT_DOMAIN="reduit.local"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Le Réduit Interactive Installer ===${NC}"

# 1. Interactive Configuration
if [ ! -f "$CONFIG_FILE" ]; then
    echo "No config found. Creating one..."
    
    read -p "Target Domain [$DEFAULT_DOMAIN]: " DOMAIN
    DOMAIN=${DOMAIN:-$DEFAULT_DOMAIN}
    
    read -p "Map Region to sync [$DEFAULT_REGION]: " REGION
    REGION=${REGION:-$DEFAULT_REGION}
    
    cat <<EOF > $CONFIG_FILE
global:
  domain: "$DOMAIN"

maps:
  enabled: true
  region: "$REGION"

matrix:
  enabled: true

meshtastic:
  enabled: true

bridge:
  enabled: true
EOF
    echo -e "${GREEN}Config saved to $CONFIG_FILE${NC}"
else
    echo -e "${GREEN}Using existing $CONFIG_FILE${NC}"
fi

# 2. Build Images
echo -e "${BLUE}[1/4] Building Docker Images...${NC}"
docker build -t le-reduit:latest ./src

# 3. Initial Helm Install (Core Services)
echo -e "${BLUE}[2/4] Deploying Core via Helm...${NC}"
# We disable the bridge initially because we don't have the token yet
helm upgrade --install le-reduit ./charts/le-reduit \
  -f $CONFIG_FILE \
  --set bridge.enabled=false \
  --wait

# 4. Matrix Bot Registration Loop
# Check if we already have a token in config
EXISTING_TOKEN=$(grep "matrixToken" $CONFIG_FILE || true)

if [[ -z "$EXISTING_TOKEN" ]]; then
    echo -e "${BLUE}[3/4] Registering Matrix Bot...${NC}"
    
    # Wait for API availability
    echo "Waiting for Matrix API..."
    kubectl port-forward svc/matrix-server 8008:8008 > /dev/null 2>&1 &
    PF_PID=$!
    trap "kill $PF_PID" EXIT
    
    sleep 5
    for i in {1..30}; do
        if curl -s http://localhost:8008/_matrix/client/versions > /dev/null; then
            break
        fi
        sleep 2
    done

    BOT_USER="reduit_bot"
    BOT_PASSWORD=$(openssl rand -base64 12)
    
    # Register
    REGISTER_RESP=$(curl -s -X POST -d "{\"username\":\"$BOT_USER\", \"password\":\"$BOT_PASSWORD\", \"auth\": {\"type\":\"m.login.dummy\"}}" "http://localhost:8008/_matrix/client/r0/register")
    ACCESS_TOKEN=$(echo $REGISTER_RESP | jq -r .access_token)
    USER_ID=$(echo $REGISTER_RESP | jq -r .user_id)
    
    if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
        echo "Registration failed. Manual intervention required."
        echo $REGISTER_RESP
        exit 1
    fi

    # Create Room
    ROOM_RESP=$(curl -s -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -d '{"name":"Le Reduit Ops", "preset":"public_chat"}' "http://localhost:8008/_matrix/client/r0/createRoom")
    ROOM_ID=$(echo $ROOM_RESP | jq -r .room_id)
    
    echo -e "${GREEN}Bot Registered ($USER_ID). Room Created ($ROOM_ID).${NC}"
    
    # Append to config.yaml
    echo "" >> $CONFIG_FILE
    echo "bridge:" >> $CONFIG_FILE
    echo "  enabled: true" >> $CONFIG_FILE
    echo "  matrixToken: \"$ACCESS_TOKEN\"" >> $CONFIG_FILE
    echo "  matrixRoom: \"$ROOM_ID\"" >> $CONFIG_FILE
else
    echo "Token already present in config. Skipping registration."
fi

# 5. Final Helm Upgrade (Enable Bridge)
echo -e "${BLUE}[4/4] Deploying Bridge...${NC}"
helm upgrade --install le-reduit ./charts/le-reduit -f $CONFIG_FILE

echo -e "${GREEN}Deployment Complete!${NC}"
