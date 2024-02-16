import React from "react";
import { useLoginStore } from "$auth/state/login";
import {
    Button,
    CircularProgress,
    FormControl,
    FormLabel,
    Input,
} from "@mui/joy";
import { ArrowLeft } from "lucide-react";

export const ForgotPassword: React.FC = () => {
    const { loading, setLoading, setPage } = useLoginStore();

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        setLoading(true);
        // const formData = new FormData(e.currentTarget);
        setLoading(false);
    };

    return (
        <form
            onSubmit={onSubmit}
            className="flex min-w-96 flex-col gap-4 rounded-md border border-slate-200 bg-slate-50 p-4"
        >
            {loading ? (
                <>
                    <CircularProgress className="animate-spin" />
                </>
            ) : (
                <>
                    <FormControl>
                        <FormLabel>Username</FormLabel>
                        <Input name="username" placeholder="admin" required />
                    </FormControl>
                    <div className="flex w-full flex-row gap-2">
                        <Button type="submit" className="w-full">
                            Send reset e-mail
                        </Button>
                        <Button
                            type="button"
                            color="neutral"
                            onClick={() => setPage("login")}
                        >
                            <ArrowLeft />
                        </Button>
                    </div>
                </>
            )}
        </form>
    );
};
