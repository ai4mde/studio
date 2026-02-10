import React from "react"
import useLocalStorage from "./useLocalStorage"
import { Switch, Typography } from "@mui/joy"
type Props = {
}

export const Settings: React.FC<Props> = () => {
    const [data, setData] = useLocalStorage("settings", { managerAccess: false})

    return (
        <>
            <Typography component="label" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Switch
                    checked={data.managerAccess}
                    onChange={(e) => setData({ ...data, managerAccess: e.target.checked })}
                    color={data.managerAccess ? "success" : "danger"}
                />
                Manager Access
            </Typography>
        </>       

    )
}