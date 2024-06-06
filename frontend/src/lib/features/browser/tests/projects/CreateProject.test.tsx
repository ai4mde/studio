import { render } from "@testing-library/react";
import CreateProject from "$browser/components/projects/CreateProject";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

test("Renders", () => {
    render(
        <QueryClientProvider client={queryClient}>
            <CreateProject />
        </QueryClientProvider>,
    );
});
