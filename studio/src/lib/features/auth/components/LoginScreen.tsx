import React, { useState } from "react";
import { useAuthStore } from "../state/auth";
import { Button, CircularProgress, FormControl, FormLabel, Input } from "@mui/joy";

const LoginScreen: React.FC = () => {
    const { login } = useAuthStore();
    const [loading, setLoading] = useState(false);

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        setLoading(true)
        const formData = new FormData(e.currentTarget);
        login(`${formData.get("username")}`, `${formData.get("password")}`)
        setLoading(false)
    };

    return (
        <div className="w-full h-full min-h-screen flex items-center justify-center bg-slate-100">
            <div className="flex flex-col gap-4 p-4">
                <h1 className="font-bold text-sm text-center">
                    AI4MDE - Studio
                </h1>
                <form
                    onSubmit={onSubmit}
                    className="flex flex-col gap-4 p-4 min-w-96 bg-slate-50 border-slate-200 border rounded-md"
                >
                    {loading ? (
                        <>
                          <CircularProgress className="animate-spin"/>
                        </>
                    ) : (
                        <>
                            <FormControl>
                                <FormLabel>Username</FormLabel>
                                <Input
                                    name="username"
                                    placeholder="admin"
                                    required
                                />
                            </FormControl>
                            <FormControl>
                                <FormLabel>Password</FormLabel>
                                <Input
                                    name="password"
                                    type="password"
                                    required
                                />
                            </FormControl>
                            <div className="w-full flex flex-row">
                                <Button type="submit" className="w-full">
                                    Login
                                </Button>
                            </div>
                        </>
                    )}
                </form>
            </div>
        </div>
    );
};

export default LoginScreen;
