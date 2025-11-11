# Multiverse 
This repository contains the source code for the Multiverse discord bot, a bot for queueing up and scrimming other players in multiple games.

## Features
- Multi-game queue system (Rainbow Six Siege, Rocket League, Valorant, Breachers)
- MMR (Matchmaking Rating) system for balanced matches
- Party system for team play
- Admin commands for match management
- Leaderboard tracking

## Docker Setup

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)
- Discord Bot Token (get one from [Discord Developer Portal](https://discord.com/developers/applications))

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Germ-99/Multiverse.git
   cd Multiverse
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f app
   ```

5. **Stop the bot**
   ```bash
   docker-compose down
   ```

### Development Mode

For development with live code reloading, uncomment the volumes section in `docker-compose.yml`:

```yaml
volumes:
  - .:/app
```

Then rebuild and restart:
```bash
docker-compose up --build
```

### Manual Docker Commands

If you prefer not to use Docker Compose:

```bash
# Build the image
docker build -t multiverse-bot .

# Run the container
docker run -d --name multiverse-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  multiverse-bot
```

### Database Persistence

The SQLite database is stored in the `./data` directory and is persisted across container restarts. Make sure this directory exists or Docker will create it automatically.

### Troubleshooting

- **Bot not starting**: Check your Discord token in the `.env` file
- **Permission errors**: Ensure the `data` directory has proper write permissions
- **Container keeps restarting**: Check logs with `docker-compose logs -f app`

## Local Development (without Docker)

If you prefer to run the bot locally:

1. **Install Python 3.12+**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

