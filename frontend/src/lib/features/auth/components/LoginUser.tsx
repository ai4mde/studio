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

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        setLoading(true);
        const formData = new FormData(e.currentTarget);
        login(`${formData.get("username")}`, `${formData.get("password")}`);
        setLoading(false);
    };

    const onDemoLogin = () => {
        setLoading(true);
        login('demo', 'demo');
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
                    <div className="flex w-full flex-row gap-1">
                        <Button type="submit" className="w-full">
                            Login
                        </Button>
                        <Button
                            type="button"
                            color="neutral"
                            className="w-full"
                            onClick={() => setPage("register")}
                        >
                            Register
                        </Button>
                    </div>
                    <div className="relative flex items-center gap-2 py-1">
                        <div className="flex-1 border-t border-slate-200" />
                        <span className="text-xs text-slate-400">or</span>
                        <div className="flex-1 border-t border-slate-200" />
                    </div>
                    <Button
                        type="button"
                        variant="outlined"
                        color="neutral"
                        className="w-full"
                        onClick={onDemoLogin}
                    >
                        Try Demo — no account needed
                    </Button>
                </>
            )}
        </form>
    );
};
