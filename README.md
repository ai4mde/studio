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

## Current thesis Code evaluator

The **one current thesis Code evaluator** is on branch `thesis-code-evaluator-final`.
Use the explicit validated scoring entry point
`evaluation.friedrich_code_v3.combined_candidate_v8.evaluate_combined_candidate_v8`.
Its [final README](evaluation/friedrich_code_v3/README.md) explains the construct and replay
contract; the [freeze manifest](evaluation/friedrich_code_v3/freeze/thesis_final_v8_20261005/final_code_v8_freeze_manifest.json)
identifies the exact validated code, inputs, and evidence. The validated **Formal Overall
Code F1 is 0.8499803891** (40 cases, 120 candidates).

**Do not use generic package imports or old runner entry points as the thesis-final
evaluator.** Use the explicit `combined_candidate_v8` entry point. V3.1, V3.2,
intermediate combined evaluators, and earlier runners are **historical / provenance
only**. Some older-named modules are still live v8 helper dependencies; keep them.
See the [evaluator navigation guide](docs/code-evaluator-navigation.md) and the
[separate public-export proposal](docs/code-evaluator-public-export-proposal.md).

## ⚡️ Quick start
To get up and running with the AI4MDE tool in no time, use the code below. For more explanations and environment requirements, read [docs/setup.md](./docs/setup.md) (you will need Docker, Git, and, if you are on Windows, WSL).

```bash
# Ensure that you have the Docker installed
docker -v
docker compose version

# Clone the repository
git clone https://github.com/ai4mde/studio.git
cd studio

# Create secrets file for storing LLM API credentials (you can leave this file unchanged for now)
cp config/secrets.env.example config/secrets.env

# Build and start all the containers (add -d flag to start in background)
docker compose up -d --build

# To stop the containers, you can use
docker compose down
```

Now visit [http://ai4mde.localhost](http://ai4mde.localhost).
<b>The login credentials can be found in `config/api.env`.</b>

- For explanations on using the diagram modelling features, see [docs/users-guide.md](./docs/users-guide.md).

- For an overview of the technical architecture, see [docs/architecture.md](./docs/architecture.md).

- You can report issues using our [bug reporting board](https://github.com/orgs/ai4mde/projects/12). This is public for viewing, but requires us to add you as a collaborator in order to post a new issue. Please, contact someone from the course support team in order to be added.
