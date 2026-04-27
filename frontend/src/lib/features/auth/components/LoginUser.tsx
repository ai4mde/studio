import React from "react";
import { useAuthStore } from "$auth/state/auth";
import {
    Button,
    CircularProgress,
    FormControl,
    FormHelperText,
    FormLabel,
    Input,
} from "@mui/joy";
import { useLoginStore } from "$auth/state/login";

export const LoginUser = () => {
    const { login } = useAuthStore();
    const { loading, setLoading, setPage } = useLoginStore();
    const [error, setError] = React.useState("");

    const onSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        const formData = new FormData(e.currentTarget);
        const result = await login(`${formData.get("username")}`, `${formData.get("password")}`);
        if (!result.ok) {
            setError(result.message || "Login failed.");
        }
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
                    <FormControl>
                        <FormLabel>Password</FormLabel>
                        <Input name="password" type="password" required />
                        <FormHelperText>
                            <button
                                type="button"
                                className="text-xs text-gray-500"
                                onClick={() => setPage("forgot")}
                            >
                                Forgot password?
                            </button>
                        </FormHelperText>
                    </FormControl>
                    {error && (
                        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                            {error}
                        </p>
                    )}
                    <div className="flex w-full flex-row gap-1">
                        <Button type="submit" className="w-full">
                            Login
                        </Button>
                        <Button
                            type="button"
                            color="neutral"
                            className="w-full"
                            onClick={() => {
                                setPage("register");
                            }}
                        >
                            Register
                        </Button>
                    </div>
                </>
            )}
        </form>
    );
};
