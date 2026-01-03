#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Le Réduit Full Stack Deployment ===${NC}"

# 1. Check Dependencies
command -v jq >/dev/null 2>&1 || { echo >&2 "I require jq but it's not installed.  Aborting."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo >&2 "I require kubectl but it's not installed.  Aborting."; exit 1; }

# 2. Build Docker Image
echo -e "${GREEN}[1/5] Building Docker Image...${NC}"
docker build -t le-reduit:latest ./src

# 3. Deploy Core Services
echo -e "${GREEN}[2/5] Deploying Core Services (Matrix & Meshtastic)...${NC}"
kubectl apply -f k8s/matrix-server.yaml
kubectl apply -f k8s/meshtastic-node.yaml

# 4. Wait for Matrix Server
echo -e "${GREEN}[3/5] Waiting for Matrix Server to be ready...${NC}"
# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app=matrix-server --timeout=120s

# Setup Port Forwarding to access Matrix API locally
echo "Starting port-forward to matrix-server..."
kubectl port-forward svc/matrix-server 8008:8008 > /dev/null 2>&1 &
PF_PID=$!

# Trap to kill port-forward on exit
trap "kill $PF_PID" EXIT

# Loop to check API availability
echo "Waiting for API to respond at localhost:8008..."
for i in {1..30}; do
    if curl -s http://localhost:8008/_matrix/client/versions > /dev/null; then
        echo "Matrix API is UP!"
        break
    fi
    sleep 2
done

# 5. Register Bot & Create Room
echo -e "${GREEN}[4/5] Configuring Matrix Bot...${NC}"
BOT_USER="reduit_bot"
BOT_PASSWORD=$(openssl rand -base64 12)

# Register
echo "Registering user: @$BOT_USER:reduit.local"
REGISTER_RESP=$(curl -s -X POST -d "{\"username\":\"$BOT_USER\", \"password\":\"$BOT_PASSWORD\", \"auth\": {\"type\":\"m.login.dummy\"}}" "http://localhost:8008/_matrix/client/r0/register")

ACCESS_TOKEN=$(echo $REGISTER_RESP | jq -r .access_token)
USER_ID=$(echo $REGISTER_RESP | jq -r .user_id)

if [ "$ACCESS_TOKEN" == "null" ]; then
    echo "Registration failed: $REGISTER_RESP"
    exit 1
fi
echo "Got Access Token."

# Create Room
echo "Creating Room: Le Reduit Ops"
ROOM_RESP=$(curl -s -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -d '{"name":"Le Reduit Ops", "preset":"public_chat"}' "http://localhost:8008/_matrix/client/r0/createRoom")
ROOM_ID=$(echo $ROOM_RESP | jq -r .room_id)

if [ "$ROOM_ID" == "null" ]; then
    echo "Room creation failed: $ROOM_RESP"
    exit 1
fi
echo "Created Room: $ROOM_ID"

# 6. Deploy Bridge
echo -e "${GREEN}[5/5] Deploying Meshtastic Bridge...${NC}"

# Apply Deployment (without ConfigMap first)
kubectl apply -f k8s/meshtastic-bridge.yaml

# Create ConfigMap dynamically
cat <<EOF > bridge-config.gen.yaml
meshtastic:
  connection_type: network
  network:
    host: "meshtastic-node"
    port: 4403
  channel: 0

matrix:
  homeserver: "http://matrix-server:8008"
  user_id: "$USER_ID"
  access_token: "$ACCESS_TOKEN"
  room_id: "$ROOM_ID"

logging:
  level: INFO
EOF

# Update ConfigMap in cluster
kubectl create configmap meshtastic-bridge-config --from-file=config.yaml=bridge-config.gen.yaml --dry-run=client -o yaml | kubectl apply -f -

# Restart pod to pick up new config
kubectl rollout restart deployment/meshtastic-bridge

echo -e "${BLUE}=== Deployment Complete ===${NC}"
echo -e "Bot User: $USER_ID"
echo -e "Room ID:  $ROOM_ID"
echo -e "Password: $BOT_PASSWORD (Safe this if you want to login manually!)"
rm bridge-config.gen.yaml
