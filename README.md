# Kick.com Unofficial API

An unofficial API wrapper for Kick.com that handles Cloudflare protection automatically. This project provides a FastAPI-based REST API that mirrors Kick.com's API endpoints while managing Cloudflare bypass seamlessly.

## Features

- 🛡️ Automatic Cloudflare protection bypass
- 🔄 Session token authentication support
- 🚀 FastAPI-powered REST API
- 📝 Comprehensive endpoint documentation
- 🔍 Error handling and logging
- ⚡ Efficient request retrying and caching

## Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)
- FastAPI
- curl-cffi

## Installation

### Option 1: Direct Installation

1. Clone the repository:
```bash
git clone https://github.com/sarperavci/kick-unofficial-api.git
cd kick-unofficial-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Deploy the Cloudflare bypass server:
```bash
docker run -d -p 8000:8000 ghcr.io/sarperavci/cloudflarebypassforscraping:latest
```

4. Run the API server:
```bash
python src/api.py
```

### Option 2: Docker Deployment

1. First, deploy the Cloudflare bypass server:
```bash
docker run -d -p 8000:8000 ghcr.io/sarperavci/cloudflarebypassforscraping:latest
```

2. Then, deploy the API server:
```bash
docker run -d -p 5000:5000 \
  -e BYPASS_SERVER_URL=http://host.docker.internal \
  -e BYPASS_SERVER_PORT=8000 \
  -e TARGET_URL=https://kick.com \
  ghcr.io/sarperavci/kick-unofficial-api:latest
```

Note: Use `host.docker.internal` to connect to the bypass server running on your host machine.

### Option 3: Docker Compose

Run:
```bash
docker-compose up -d
```

## Configuration

The API configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| BYPASS_SERVER_URL | Cloudflare bypass server URL | http://localhost |
| BYPASS_SERVER_PORT | Bypass server port | 8000 |
| TARGET_URL | Target API base URL | https://kick.com |

## API Documentation

Once running, access the Swagger UI documentation at:
- Local deployment: `http://localhost:5000/docs`
- Docker deployment: `http://your-server:5000/docs`

### Authentication

For endpoints requiring authentication, include your Kick.com session token in the Authorization header:
```bash
curl -H "Authorization: Bearer your-session-token" http://localhost:5000/api/v2/...
```

## Available Endpoints

![](https://github.com/user-attachments/assets/79e41f1b-43a0-465f-8acc-ad521d456491)

## API Endpoint Discovery

The project includes a mitmproxy script (`misc/endpoint_discovery.py`) for discovering new Kick.com API endpoints:

1. Install mitmproxy requirements:
```bash
pip install -r misc/requirements.txt
```

2. Run mitmproxy with the discovery script:
```bash
mitmproxy -s misc/endpoint_discovery.py
```

The script will automatically capture and document API requests/responses in the `api_docs` directory.

## Development

### Building the Docker Image

```bash
docker build -t kick-unofficial-api .
```

## Contributing

Contributions are welcome! Please feel free to submit a PR. Endpoints are not complete yet.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [CloudflareBypassForScraping](https://github.com/sarperavci/CloudflareBypassForScraping/) for the Cloudflare bypass solution
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [curl-cffi](https://github.com/lexiforest/curl_cffi) for HTTP request handling to bypass Cloudflare SSL Fingerprinting
- [mitmproxy](https://mitmproxy.org/) for endpoint discovery

## Disclaimer

This project is not affiliated with or endorsed by Kick.com. Use responsibly and in accordance with Kick.com's terms of service.
