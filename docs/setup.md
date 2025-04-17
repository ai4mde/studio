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

Get up and running with the AI4MDE studio and API in no time:

```
git clone https://github.com/ai4mde/studio.git
cd frontend
docker-compose up -d
```

Now visit [http://ai4mde.localhost](http://ai4mde.localhost)

<br/>

## Installation

> ☝️ This project is assumes you run a GNU/Linux system.
> If you find yourself on Windows, please work from WSL2.
> You should be fine on macOS. If you're just running without
> contributing, ignore the above.

The easiest way to get started is through a container runtime and the docker compose file at the root. If these terms are unfamiliar to you, start with installing a container runtime.

Before the environment can be built, secret API keys need to be specified in `/config/secrets.env`. An example of such a file can be seen in `/config/secrets.env.example`.

With everything ready and this repository cloned, you can get started from a shell:

```bash
# Ensure that you have the correct tools installed, you might have to restart
# your shell
docker -v
docker compose version

# Build all the necessary images (only required on first install or dependency change)
docker compose build

# Start all the containers (add -d flag to start in background)
docker compose up
```

This will start multiple services in the background and set everything up (for development). As soon as that's done, you can find the following services on your machine's network:

- [ai4mde.localhost](http://ai4mde.localhost) - Frontend, from `/frontend`
- [api.ai4mde.localhost](http://api.ai4mde.localhost) - API from `/api`
- [prototype.ai4mde.localhost](http://prototype.ai4mde.localhost) - Running prototype in `/prototypes/generated_prototypes`
- [prototypes_api.ai4mde.localhost](http://prototypes_api.ai4mde.localhost) - Prototype management API from `/prototypes/backend`
