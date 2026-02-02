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

> ☝️ Depending on your operating system, you should set up your envirnoment to meet the following requirements:
>    - For <b>Windows</b>, please work from <b>WSL 2.1.5</b> or higher ([installation guide](https://learn.microsoft.com/en-us/windows/wsl/install)),
> and set up <b>Docker Desktop</b> accordingly ([instructions](https://docs.docker.com/desktop/features/wsl/)).
>    - For a <b>Linux</b> distribution, you may use a regular terminal. Make sure you have installed <b>Docker Engine</b>
> ([guides](https://docs.docker.com/engine/install/)) or <b>Docker Desktop</b> ([guides](https://docs.docker.com/desktop/setup/install/linux/)).
>    - For <b>macOS</b>, you should be able to use a regular terminal. Make sure you have installed or <b>Docker Desktop</b>
> ([installation guide](https://docs.docker.com/desktop/setup/install/mac-install/)).

> ☝️ Make sure <b>Git</b> is installed on your device ([instructions](https://github.com/git-guides/install-git)).

> ☝️ If you are using <b>Docker Desktop</b>, make sure it is running on your device before using the commands below in your terminal.

With these requirements met, you can get started from a Linux, macOS or WSL terminal:

```bash
# Ensure that you have the Docker installed
docker -v
docker compose version

# Clone the repository
git clone https://github.com/ai4mde/studio.git
cd studio
```

Before the environment can be built, you need to provide your secret OpenAI and Groq API keys in `/config/secrets.env`. An example of such a file can be seen in `/config/secrets.env.example`. You have to perform this step in order to run the software, however you may leave the values empty if you are not interested in using the LLM features. Feel free to use the terminal or any code/text editor for this step.

Also, take note of the username and password stored in files `config/api.env` and `config/prototypes.env`. These are your credentials for logging into AI4MDE, and any potential web application prototypes you might generate with it, respectively: `DJANGO_SUPERUSER_USERNAME = admin` and `DJANGO_SUPERUSER_PASSWORD = sequoias`. You may update your credentials in these files if you wish.

```bash
# Configure secrets (required file; values optional if you won't use LLM features)
cp config/secrets.env.example config/secrets.env
# edit config/secrets.env
# edit config/api.env
# edit config/prototypes.env

# Build and Start all the containers (add -d flag to start in background)
docker compose up -d --build

# To stop the containers, you can use
docker compose down
```

This will start multiple services in the background and set everything up (for development). As soon as that's done, you can find the following services on your machine's network:

- [ai4mde.localhost](http://ai4mde.localhost) - Frontend, from `/frontend`. As a non-contributing user, this is where you can interact with the AI4MDE tool.
- [api.ai4mde.localhost](http://api.ai4mde.localhost) - API from `/api`
- [prototype.ai4mde.localhost](http://prototype.ai4mde.localhost) - Running prototype in `/prototypes/generated_prototypes`
- [prototypes_api.ai4mde.localhost](http://prototypes_api.ai4mde.localhost) - Prototype management API from `/prototypes/backend`
