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
                        <Button type="submit" className="w-full" name="login">
                            Login
                        </Button>
                        <Button
                            type="button"
                            color="neutral"
                            className="w-full"
                            onClick={() => {
                                setPage("register");
                            }}
                            name="register"
                        >
                            Register
                        </Button>
                    </div>
                </>
            )}
        </form>
    );
};
