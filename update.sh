#!/bin/bash

# Usage: ./check_poetry_package.sh <package> <version>

PACKAGE=$1
VERSION=$2

if [[ -z "$PACKAGE" || -z "$VERSION" ]]; then
  echo "Usage: $0 <package> <version>"
  exit 1
fi

# Function to clear Poetry cache
clear_poetry_cache() {
  echo "Clearing Poetry cache for $PACKAGE..."
  poetry cache clear pypi --all
}

# Function to check if the package with the version is available
check_package_version() {
  echo "Searching for package $PACKAGE..."
  poetry search "$PACKAGE" | grep -q "$VERSION"
  return $?
}

# Step 1: Clear cache
clear_poetry_cache

# Step 2 & 3: Check for version in search output, retry if not found
MAX_RETRIES=5
RETRY_DELAY=5

for ((i=1; i<=MAX_RETRIES; i++)); do
  if check_package_version; then
    echo "Found $PACKAGE version $VERSION."
    break
  else
    echo "Version $VERSION not found for $PACKAGE. Attempt $i/$MAX_RETRIES."
    clear_poetry_cache
    sleep $RETRY_DELAY
  fi

  if [[ $i -eq $MAX_RETRIES ]]; then
    echo "Failed to find $PACKAGE version $VERSION after $MAX_RETRIES attempts."
    exit 1
  fi
done

# Step 4: Update poetry lock file
echo "Updating Poetry lock file..."
poetry update --lock

# Step 5: Install dependencies
echo "Installing dependencies..."
poetry install

echo "Done."