<p align="center">
    <img
        src="https://avatars.githubusercontent.com/u/155311177"
        alt="AI4MDE Studio"
        width="64"
    />
</p>

<h1 align="center">
  AI4MDE &middot; <b>Studio</b>
</h1>

<div align="center">
  <strong>AI4MDE Back-end & Editor</strong>
</div>

<p align="center">
  Repository with the central component of the AI4MDE System.
</p>

<br/>

## ⚡️ Quick start

> ☝️ This project is assumes you run a GNU/Linux system.
> If you find yourself on Windows, please work from WSL2.
> You should be fine on macOS. If you're just running without
> contributing, ignore the above.

The easiest way to get started is through a container runtime and the docker compose
file at the root. If these terms are unfamiliar to you, start with installing a container
runtime. We recommend the permissive-licensed [Rancher Desktop](https://rancherdesktop.io/),
when asked use the `dockerd` backend instead of `containerd`.

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

This will start multiple services in the background and set everything up (for development).
As soon as that's done, you can find the following services on your machine's network:

- [ai4mde.localhost](http://ai4mde.localhost) - Studio, from `./studio`
- [api.ai4mde.localhost](http://api.ai4mde.localhost) - API from `./model`
- [docs.ai4mde.localhost](http://docs.ai4mde.localhost) - Docs from `./docs`

## Development Documentation

Even though you can run the entire suite in docker, we recommend installing local
dependencies for development. Especially using tools such as git hooks or using an
integrated development environment is easier if you have the necessary binaries
installed locally.

You can install a supported python distribution locally with [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)
and use [pipx](https://github.com/pypa/pipx?tab=readme-ov-file#install-pipx) to use
a virtual environment to install poetry. After you have `python >= 3.10` and `pipx`
installed you can install poetry and setup the dependencies:

```bash
pipx install poetry
cd model && poetry install
cd ..

cd docs && poetry install
cd ..
```

For our JavaScript applications, we use `bun` as a runtime. You can easily install
bun with the following one-liner:

```bash
curl -fsSL https://bun.sh/install | bash
```

Then, install the dependencies in studio:

```bash
cd studio
bun install
```
