import React from "react";
import { LoginUser } from "./LoginUser";
import { ForgotPassword } from "./ForgotPassword";
import { RegisterUser } from "./RegisterUser";
import { useLoginStore } from "$auth/state/login";

const LoginScreen: React.FC = () => {
    const { page } = useLoginStore();

    return (
        <div className="flex h-full min-h-screen w-full items-center justify-center bg-slate-100">
            <div className="flex flex-col gap-4 p-4">
                <h1 className="text-center text-sm font-bold">
                    AI4MDE - Studio
                </h1>
                {page == "login" && <LoginUser />}
                {page == "register" && <RegisterUser />}
                {page == "forgot" && <ForgotPassword />}
            </div>
        </div>
    );
};

export default LoginScreen;
