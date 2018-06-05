#Configure Keystoneng module
cat > keystone_details.txt << EOF
keystone:
  auth:
    username: $OS_USERNAME
    password: $OS_PASSWORD
    user_domain_name: default
    project_name: admin
    project_domain_name: default
    auth_url: $OS_AUTH_URL
  identity_api_version: 3
EOF
