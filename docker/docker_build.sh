echo Building REST API Server...
docker build -t mdt_rest_api_server -f Dockerfile_rest_api_server .

echo Building Meeting Server..
docker build -t mdt_meeting_server -f Dockerfile_meeting_server .

echo Pushing REST API server to repo (must be logged into docker account)...
docker tag mdt_rest_api_server:latest bakshi41c/mdt_rest_api_server:latest
docker push bakshi41c/mdt_rest_api_server:latest

echo Pushing Meeting server to repo (must be logged into docker account)...
docker tag mdt_meeting_server:latest bakshi41c/mdt_meeting_server:latest
docker push bakshi41c/mdt_meeting_server:latest