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

> ☝️ If you are working on <b>Windows</b>, please work from WSL 2.1.5 or higher ([instalaltion guide](https://learn.microsoft.com/en-us/windows/wsl/install)),
> and set up Docker Desktop accordingly ([instructions](https://docs.docker.com/desktop/features/wsl/)).

> ☝️ If you are working on a <b>Linux</b> distribution, you may use a regular terminal. Make sure you have installed Docker Engine
> ([guides](https://docs.docker.com/engine/install/)) or Docker Desktop ([guides](https://docs.docker.com/desktop/setup/install/linux/)).

> ☝️ If you are working on <b>macOS</b>, you may should be able to use a regular terminal. Make sure you have installed or Docker Desktop
> ([guides](https://docs.docker.com/desktop/setup/install/mac-install/)).

> ☝️ If you are using Docker Desktop, make sure this is running on your device before using the commands below in your terminal.

With your environment correctly set up, you can get started from a Linux, macOS or WSL terminal:

```bash
# Ensure that you have the Docker installed
docker -v
docker compose version

# Clone the repository
git clone https://github.com/ai4mde/studio.git

# Go to the root directory
cd studio
```

Before the environment can be built, you need to provide your secret OpenAI and Groq API keys in `/config/secrets.env`. An example of such a file can be seen in `/config/secrets.env.example`. You have to perform this step in order run the software, however you may leave the values empty if you are not interested in using the LLM features. Feel free to use the terminal or any code/text editor for this step.

```bash
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
