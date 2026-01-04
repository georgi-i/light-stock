# Docker Deployment Guide

This guide explains how to deploy LightStock using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/georgi-i/light-stock.git
cd light-stock
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.docker .env

# Edit with your settings
nano .env  # or vim, code, etc.
```

**Important:** Change these values in `.env`:
- `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `SECURITY_PASSWORD_SALT` - Generate with: `python -c "import secrets; print(secrets.token_hex(16))"`
- `SECURITY_TOTP_SECRETS` - Generate with: `python -c "import secrets; print('{\"1\": \"' + secrets.token_hex(16) + '\"}')"`

### 3. Build and Run

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f lightstock
```

The application will be available at **http://localhost:8000**

### 4. Initialize Database

```bash
# Create admin user
docker-compose exec lightstock python init_db.py
```

Follow the prompts to create your admin account.

## Docker Compose Profiles

### Basic Setup (App Only)

```bash
docker-compose up -d
```

Runs only the LightStock application on port 8000.

### With Nginx Reverse Proxy

```bash
docker-compose --profile with-nginx up -d
```

Runs the application with Nginx as a reverse proxy on ports 80/443.

## Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f lightstock
```

### Restart Services

```bash
docker-compose restart
```

### Stop Services

```bash
docker-compose stop
```

### Remove Everything

```bash
docker-compose down
docker volume prune
```

### Access Container Shell

```bash
docker-compose exec lightstock bash
```

### Run Database Commands

```bash
# Initialize database
docker-compose exec lightstock python init_db.py

# Access Python shell
docker-compose exec lightstock python
```

## Production Deployment

### 1. Use Environment Variables

Never commit `.env` to git. Use Docker secrets or environment variables:

```bash
export SECRET_KEY="your-secret-key"
export SECURITY_PASSWORD_SALT="your-salt"
docker-compose up -d
```

### 2. Enable HTTPS with Nginx

Update `docker-compose.yml` to use the nginx profile:

```bash
docker-compose --profile with-nginx up -d
```

Configure SSL in `deploy/nginx.conf`.

### 3. Persistent Data

Data is stored in Docker volumes:
- `./instance` - SQLite database
- `./logs` - Application logs

Backup these directories regularly.

### 4. Health Checks

The container includes health checks:

```bash
docker-compose ps
```

Check the "Status" column for health information.

## Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs lightstock

# Check container status
docker-compose ps
```

### Database Issues

```bash
# Reset database (WARNING: Deletes all data)
docker-compose down
rm -rf instance/
docker-compose up -d
docker-compose exec lightstock python init_db.py
```

### Permission Issues

```bash
# Fix permissions
sudo chown -R 1000:1000 instance/
sudo chown -R 1000:1000 logs/
```

### Port Already in Use

Change the port in `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Use port 8080 instead
```

## Advanced Configuration

### Using PostgreSQL

1. Add PostgreSQL to `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ims_db
      POSTGRES_USER: ims_user
      POSTGRES_PASSWORD: ims_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - lightstock-network

volumes:
  postgres_data:
```

2. Update `.env`:

```bash
DATABASE_URL=postgresql://ims_user:ims_password@postgres:5432/ims_db
```

### Custom Gunicorn Configuration

Edit `gunicorn.conf.py` to customize workers, timeouts, etc.

### Resource Limits

Add to service in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '1'
      memory: 512M
```

## Security Best Practices

1. **Use secrets management** for production (Docker secrets, HashiCorp Vault)
2. **Run behind a reverse proxy** (Nginx, Traefik)
3. **Enable HTTPS** with Let's Encrypt
4. **Regular backups** of instance/ directory
5. **Keep Docker images updated** (`docker-compose pull`)
6. **Use non-root user** (already configured in Dockerfile)
7. **Scan images for vulnerabilities** (`docker scan lightstock:latest`)

## Building for Production

### Multi-architecture Build

```bash
# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t lightstock:latest .
```

### Push to Registry

```bash
# Tag image
docker tag lightstock:latest your-registry/lightstock:latest

# Push to registry
docker push your-registry/lightstock:latest
```

## Monitoring

### Container Stats

```bash
docker stats lightstock-app
```

### Health Status

```bash
docker inspect --format='{{.State.Health.Status}}' lightstock-app
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/georgi-i/light-stock/issues
- Documentation: [README.md](README.md)
