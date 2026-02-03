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
To get up and running with the AI4MDE tool in no time, use the code below. For more explanations and environment requirements, read [docs/setup.md](./docs/setup.md) (you will need Docker, Git, and, if you are on Windows, WSL).

```bash
# Ensure that you have the Docker installed
docker -v
docker compose version

# Clone the repository
git clone https://github.com/ai4mde/studio.git
cd studio

# Create secrets file
cp config/secrets.env.example config/secrets.env
# If you want, you can edit config/secrets.env, config/api.env, or config/prototypes.env at this point

# Build and Start all the containers (add -d flag to start in background)
docker compose up -d --build

# To stop the containers, you can use
docker compose down
```

Now visit [http://ai4mde.localhost](http://ai4mde.localhost)
The login credentials can be found in `config/api.env`.

For explanations on using the diagram modelling features, see [docs/users-guide.md](./docs/users-guide.md).

For an overview of the technical architecture, see [docs/architecture.md](./docs/architecture.md)

You can report issues using our [bug reporting board](https://github.com/orgs/ai4mde/projects/12). This is public for viewing, but requires us to add you as a collaborator in order to post a new issue. Please, contact someone from the course support team in order to be added.
