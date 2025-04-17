export const externalModels = [
    {
        title: "llama",
        version: "3.3-70b-versatile",
        author: "Meta",
        type: "metadata",
        url: "llama-3.3-70b-versatile",
        disabled: false,
    }
]

export const models = [
    {
        title: "UML Classes",
        version: "0.0.1",
        author: "",
        type: "metadata",
        url: "http://tiantian-class.ai4mde-prose.localhost/run_nlp/",
        disabled: true,
    },
    {
        title: "UML Activities",
        version: "0.0.1",
        author: "",
        type: "metadata",
        url: "http://griffioen-activity.ai4mde-prose.localhost/run_nlp/",
        disabled: true,
    },
    {
        title: "UML Usecase",
        version: "0.0.1",
        author: "",
        type: "metadata",
        url: "http://roussou-usecase.ai4mde-prose.localhost/run_nlp/",
        disabled: true,
    },
    {
        title: "Bucketing",
        type: "bucketing",
        version: "0.0.1",
        author: "",
        url: "http://martijn-bucketing.ai4mde-prose.localhost/run_nlp/",
        disabled: true,
    },
]; // TODO: Make mutable and find a way to dynamically populate this, maybe with a model registry?
