# Scheduled Events API
Provides API access to Script Kitties events managed through Discord.

## Environment Variables
A `.env` file is needed to set the bot token and server ID. Create it with the following format:

```
SERVER_ID=<server_id>
BOT_TOKEN=<bot_token>
```

## Docker
Start the service with either docker or docker-compose.

```
docker run -p 5000:5000 --env-file .env scheduled-events-api:latest
```
or
```
docker-compose up -d
```

It can then be access through http://127.0.0.1:5000.
