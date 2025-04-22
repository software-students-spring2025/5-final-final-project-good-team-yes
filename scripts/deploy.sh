#!/bin/bash

# Create project directory on Digital Ocean
ssh -i ~/.ssh/id_rsa $DIGITAL_OCEAN_USER@$DIGITAL_OCEAN_HOST << 'EOF'
  mkdir -p /opt/sandwich-tracker
  cd /opt/sandwich-tracker
EOF

# Copy docker-compose.yml to Digital Ocean
scp -i ~/.ssh/id_rsa docker-compose.yml $DIGITAL_OCEAN_USER@$DIGITAL_OCEAN_HOST:/opt/sandwich-tracker/

# Create .env file on Digital Ocean (for environment variables)
ssh -i ~/.ssh/id_rsa $DIGITAL_OCEAN_USER@$DIGITAL_OCEAN_HOST << 'EOF'
  cat > /opt/sandwich-tracker/.env << 'ENVFILE'
  MONGO_INITDB_DATABASE=sandwich_db
  DIGITAL_OCEAN_HOST=localhost
  ENVFILE
EOF

# Start the services
ssh -i ~/.ssh/id_rsa $DIGITAL_OCEAN_USER@$DIGITAL_OCEAN_HOST << 'EOF'
  cd /opt/sandwich-tracker
  docker-compose pull
  docker-compose up -d
EOF

echo "Deployment completed successfully!" 