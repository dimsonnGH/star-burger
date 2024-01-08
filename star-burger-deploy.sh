#!/bin/bash
#stop if error
set -e

# activate virtual enviroment
source venv/bin/activate

# load repository
git pull

# load python libraries
pip install -r requirements.txt

# install node.js libraries
npm install --include=dev

# build js application
npx parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

# collect static files
python3 manage.py collectstatic --noinput

# run migrations
python3 manage.py makemigrations --dry-run --check
python3 manage.py migrate --noinput

#restart application
systemctl restart star-burger.service

#reload nginx
systemctl reload nginx.service

#send notification to rollbar
export $(grep -v "^#" .env | grep 'ROLLBAR_ACCESS_TOKEN' | xargs)
curl -H "X-Rollbar-Access-Token: $ROLLBAR_ACCESS_TOKEN" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d "{\"environment\": \"production\", \"revision\": \"'$(git rev-parse --short HEAD)'\", \"rollbar_name\": \"muhabura\", \"local_username\": \"muhabura\", \"comment\": \"'$(git show -s --format=%s)'\", \"status\": \"succeeded\"}"

echo -e "\nThe deploy is done"