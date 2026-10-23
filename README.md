<p align="center">
    <img
        src="https://avatars.githubusercontent.com/u/155311177"
        alt="AI4MDE studio"
        width="64"
    />
</p>

<h1 align="center">
  AI4MDE &middot; <b>Studio</b>
</h1>

<div align="center">
  <strong>AI4MDE API & Editor</strong>
</div>

<br/>

AI4MDE is an open-source research initiative at [LIACS](https://liacs.leidenuniv.nl/) that aims to bridge the gap between AI and Model-Driven Engineering. AI4MDE is a web-based environment in which users can design and manage UML Class, Activity, and Use Case Diagrams via a user-friendly interface. The platform provides the option to generate fully functional Django software prototypes from these diagrams.  

## ⚡️ Quick start
To get up and running with the AI4MDE tool in no time, use the code below. For more explanations and environment requirements, read [setup](./docs/guides/source/setup.md) (you will need Docker, Git, and, if you are on Windows, WSL).

This delivery defaults to **real AI calls** for generated prototypes (`AI_RUNTIME_FAKE=0`). Configure your own provider keys before using the Library AI actions, or select fake mode as described below.

```bash
# Ensure that you have the Docker installed
docker -v
docker compose version

# Clone the delivery branch
git clone --branch s4386299-thesis-clean https://github.com/ai4mde/studio.git
cd studio

# Create a local credentials file without overwriting an existing one
if [ ! -f config/secrets.env ]; then
  cp config/secrets.env.example config/secrets.env
fi

# Before starting: fill in your own OPENAI_API_KEY and GROQ_API_KEY in
# config/secrets.env, or set AI_RUNTIME_FAKE=1 in config/prototypes.env.

# Build and start all the containers (add -d flag to start in background)
docker compose up -d --build

# To stop the containers, you can use
docker compose down
```

The clone command selects the published `s4386299-thesis-clean` branch. Local changes and commits that have not been pushed are not included in a fresh clone.

Now visit [http://ai4mde.localhost](http://ai4mde.localhost).
<b>The login credentials can be found in `config/api.env`.</b>

- For explanations on using the diagram modelling features, see the [user guide](./docs/guides/source/users-guide.md).

- For an overview of the technical architecture, see [architecture](./docs/guides/source/architecture.md).

- The [current Library example](./examples/library/bl1.2/README.md) includes the Studio project file and reproducible validation inputs.

- For current validation commands and the historical archive index, see [validation notes](./docs/evidence/readme.md).

## AI credentials and modes

`config/secrets.env` is a local, Git-ignored file. The committed example contains empty key values; cloning this branch does not supply the author's keys. Each operator must provide their own credentials, and real requests use that operator's provider account. Both Studio API and the prototype service load this file. Do not include it when sharing a folder or archive.

With `AI_RUNTIME_FAKE=0`, Library risk assessment and reading-plan actions call the configured providers. Missing or invalid credentials cause the AI action to fail; they do not select fake mode automatically. The successful Library smoke performs five external calls: two risk assessments and three reading-plan steps.

To try the generated Library without provider calls, change `AI_RUNTIME_FAKE` to `1` in your local `config/prototypes.env`. Keep `config/secrets.env` present; its key values may remain empty. Apply the environment change with:

```bash
docker compose up -d studio-prototypes
```

Then select **Run** for the prototype again in Studio. Set the value back to `0` and repeat these steps to return to real mode. Fake mode supplies fixed demonstration responses and does not perform model inference. This switch controls the generated prototype runtime; it does not disable every LLM feature in the Studio editor.

The automated fake validation explicitly sets its own runtime mode, so it remains fake even when the delivery default is real. Real validation is a separate, explicit `--mode real` run; see [validation notes](./docs/evidence/readme.md).

## PostgreSQL and persistent data

Compose pins the verified PostgreSQL **18.3** image by multi-platform digest. It retains the named volume mounted at `/var/lib/postgresql`, with database files under `/var/lib/postgresql/18/docker`. Keep the version and volume layout together when updating the database image; this configuration does not migrate databases from older PostgreSQL major versions.

`docker compose down` preserves the named database volume. Do not use `down -v` to switch AI modes or apply configuration changes: it removes that volume. Generated Library databases are separate SQLite files under the ignored `prototypes/generated_prototypes/` directory.

- You can report issues using our [bug reporting board](https://github.com/orgs/ai4mde/projects/12). This is public for viewing, but requires us to add you as a collaborator in order to post a new issue. Please, contact someone from the course support team in order to be added.
