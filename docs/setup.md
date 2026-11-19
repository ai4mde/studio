<p align="center">
    <img
        src="https://avatars.githubusercontent.com/u/155311177"
        alt="AI4MDE studio"
        width="64"
    />
</p>

<h1 align="center">
  AI4MDE &middot; <b>Installation Guide</b>
</h1>

## 1. Requirements

Depending on your operating system, you should set up your envirnoment to meet the following requirements:
| | Windows | Linux | macOS |
|---|---|---|---|
| Terminal | [WSL 2](https://learn.microsoft.com/en-us/windows/wsl/install) (Ubuntu) | any terminal | any terminal |
| Docker | [Docker Desktop](https://docs.docker.com/desktop/features/wsl/) with WSL integration turned on | [Docker Engine](https://docs.docker.com/engine/install/) or Docker Desktop | [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) |
| Git | inside WSL | yes | yes |

Only if you work on the frontend: [Node.js](https://nodejs.org/) 20 or newer.

Check that [Git](https://github.com/git-guides/install-git) is installed on your device.

> ☝️ If you are using <b>Docker Desktop</b>, make sure it is running on your device before using the commands below in your terminal.

With these requirements met, you can get started from a Linux, macOS or WSL terminal:

```bash
# Ensure that you have everything installed
docker -v
docker compose version
git --version

# Clone the repository
git clone https://github.com/ai4mde/studio.git
cd studio
```

## 2. Configuration

All settings are in `config/`. Only one file has to be created:

```bash
cp config/secrets.env.example config/secrets.env
```

`config/secrets.env` holds the API keys for the AI features (generating attributes and methods, prose). **Never commit this file.** You can leave the values empty if you won't use those features. To use them, fill in one or both keys:

```bash
OPENAI_API_KEY="sk-..."     # OpenAI (the example file still calls this OPENAI_KEY, use OPENAI_API_KEY)
GROQ_API_KEY="gsk_..."      # Groq, free keys at https://console.groq.com/keys
```

The OpenAI key needs credit on the account, otherwise generation fails.

The login details are in `config/api.env` (`DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD`). Generated prototypes use the ones in `config/prototypes.env`. You can change them before the first start.

```bash
edit config/secrets.env
edit config/api.env
edit config/prototypes.env
```

## 3. Start

Build and Start all the containers (add -d flag to start in background)
```bash
docker compose up -d --build
```



This will start multiple services in the background and set everything up (for development). As soon as that's done, you can find the following services on your machine's network:
| Address | What |
|---|---|
| [ai4mde.localhost](http://ai4mde.localhost) | The editor. Log in with the credentials from `config/api.env` |
| [api.ai4mde.localhost/api/v1/docs](http://api.ai4mde.localhost/api/v1/docs) | API documentation, where you can try every endpoint |
| [prototype.ai4mde.localhost](http://prototype.ai4mde.localhost) | The running generated prototype |
| [prototypes_api.ai4mde.localhost](http://prototypes_api.ai4mde.localhost) | Prototype management API |
| [localhost:8080](http://localhost:8080) | Traefik dashboard, shows which services are reachable |

To stop the containers, you can use
```bash
docker compose down
```