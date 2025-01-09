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

The easiest way to get started is through a container runtime and the docker compose file at the root. If these terms are unfamiliar to you, start with installing a container runtime. We recommend the permissive-licensed [Rancher Desktop](https://rancherdesktop.io/), when asked use the `dockerd` backend instead of `containerd`.

With everything ready and this repository cloned, you can get started from a shell:

```bash
# Ensure that you have the correct tools installed, you might have to restart
# your shell / system after installing Rancher Desktop
docker -v
docker compose version

# Build all the necessary images (only required on first install or dependency change)
docker compose build

# Start all the containers (add -d flag to start in background)
docker compose up
```

This will start multiple services in the background and set everything up (for development). As soon as that's done, you can find the following services on your machine's network:

- [ai4mde.localhost](http://ai4mde.localhost) - Frontend, from `./frontend`
- [api.ai4mde.localhost](http://api.ai4mde.localhost) - API from `./api`

## Development outside of containers

Even though you can run the entire suite in docker, we recommend installing local dependencies for development. Especially using tools such as git hooks or using an integrated development environment is easier if you have the necessary binaries installed locally.

You can install a supported python distribution locally with [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) and use [pipx](https://github.com/pypa/pipx?tab=readme-ov-file#install-pipx) to use a virtual environment to install poetry. After you have `python >= 3.10` and `pipx` installed you can install poetry and setup the dependencies:

```bash
pipx install poetry
cd api && poetry install
cd ..

cd docs && poetry install
cd ..
```

For our JavaScript applications, we use `bun` as a runtime. You can easily install bun with the following one-liner:

```bash
curl -fsSL https://bun.sh/install | bash
```

Then, install the dependencies in frontend:

```bash
cd frontend
bun install
cd ..
```

Finally, you can run the frontend using bun:

```bash
cd frontend && frontend_HOST="http://localhost:8000" bun dev
```

And you can run the server using poetry (in another shell):

```bash
cd api
poetry shell
POSTGRES_HOST=localhost ./model/manage.py runserver
```